import cv2
import subprocess
import numpy as np
from ultralytics import solutions, YOLO
import psutil
import time
import csv
import queue
import threading
import os
import json
from datetime import datetime

# ── Config ────────────────────────────────────
MODEL_PATH = os.environ.get('MODEL_PATH', '/home/jetson/best_y11.engine')
RTSP_URL   = "rtsp://localhost:8554/stream"
WIDTH, HEIGHT  = 640, 480
PROC_W, PROC_H = 640, 480
FPS            = 30
GROUND_TRUTH   = 300   # 100 pasadas × 3 clases
MAX_FRAMES     = 2000
INFERENCE_SAMPLE_EVERY = 60

# ── Zona — línea horizontal de punta a punta ──
ZONE = np.array([[20, 240], [620, 240]])

# ── CSV ───────────────────────────────────────
timestamp_inicio = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"/home/jetson/benchmark_{timestamp_inicio}.csv"
csv_file   = open(csv_filename, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'frame', 'timestamp',
    'fps',
    'lat_total_ms',
    'lat_yolo_ms',
    'lat_overhead_ms',
    'lat_inference_ms',
    'cpu_pct', 'gpu_pct', 'ram_pct', 'temp_c',
    'in_count', 'out_count', 'classwise_counts'
])

# ── Helpers ───────────────────────────────────
def get_temp():
    try:
        with open('/sys/devices/virtual/thermal/thermal_zone0/temp') as f:
            return int(f.read()) / 1000
    except:
        return 0.0

def get_gpu_load():
    paths = [
        '/sys/devices/gpu.0/load',
        '/sys/devices/platform/gpu.0/load',
        '/sys/devices/platform/bus@0/17000000.gpu/load',
    ]
    for p in paths:
        try:
            with open(p) as f:
                return int(f.read().strip()) / 10.0
        except:
            continue
    return 0.0

# ── Modelos ───────────────────────────────────
counter = solutions.ObjectCounter(
    model=MODEL_PATH,
    region=ZONE,
    show=False,
    show_in=False,
    show_out=False,
    conf=0.3,
    iou=0.5,
    verbose=False
)
print(f"✅ Counter cargado: {MODEL_PATH}")
# Deshabilitar el panel de estadísticas dibujado por Ultralytics
counter.display_counts = lambda im0: im0

# Modelo crudo para muestreo de inferencia pura
model_raw = YOLO(MODEL_PATH)
_ = model_raw(
    np.zeros((PROC_H, PROC_W, 3), dtype=np.uint8),
    conf=0.3, iou=0.5, verbose=False
)
print(f"✅ Modelo raw cargado para muestreo de inferencia")

# ── FFmpeg → MediaMTX ─────────────────────────
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-f', 'rawvideo', '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', f'{WIDTH}x{HEIGHT}',
    '-r', str(FPS),
    '-i', '-',
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-pix_fmt', 'yuv420p',
    '-f', 'rtsp',
    '-rtsp_transport', 'tcp',
    RTSP_URL
]
ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE,
                          stderr=subprocess.DEVNULL)

# ── Thread FFmpeg ─────────────────────────────
frame_queue = queue.Queue(maxsize=2)

def ffmpeg_writer():
    while True:
        frame = frame_queue.get()
        if frame is None:
            break
        try:
            ffmpeg.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("❌ FFmpeg pipe rota")
            break

writer_thread = threading.Thread(target=ffmpeg_writer, daemon=True)
writer_thread.start()


# ── Cámara ────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)

if not cap.isOpened():
    print("❌ Error: No se pudo acceder a la cámara")
    exit()

print(f"📺 Stream: http://192.168.0.172:8889/stream")
print(f"📋 CSV:    {csv_filename}")
print(f"🎯 GT:     {GROUND_TRUTH} (100 × 3 clases)")
print(f"▶ Corriendo hasta Detener desde el dashboard...")

# ── Estado ────────────────────────────────────
frame_count       = 0
last_in_count     = 0
fps_list          = []
temp_list         = []
inference_samples = []
frames_dropped    = 0

cpu_percent = 0.0
ram_percent = 0.0
gpu_percent = 0.0
temp        = 0.0

try:
    while frame_count < MAX_FRAMES:
        t_captura = time.time()

        success, frame = cap.read()
        if not success:
            print("❌ Error al leer frame")
            break

        frame_count += 1

        # Métricas de sistema cada 10 frames
        if frame_count % 10 == 0:
            cpu_percent = psutil.cpu_percent()
            ram_percent = psutil.virtual_memory().percent
            gpu_percent = get_gpu_load()
            temp        = get_temp()
            temp_list.append(temp)

        frame_small = cv2.resize(frame, (PROC_W, PROC_H),
                                  interpolation=cv2.INTER_LINEAR)

        # ─── Inferencia pura muestreada ───────
        inference_ms = ''
        if frame_count % INFERENCE_SAMPLE_EVERY == 0:
            t_inf = time.time()
            _ = model_raw(frame_small, conf=0.3, iou=0.5, verbose=False)
            inference_ms = round((time.time() - t_inf) * 1000, 2)
            inference_samples.append(inference_ms)

        # ─── ObjectCounter ────────────────────
        t_yolo = time.time()
        processed_small = counter.count(frame_small)
        yolo_ms = (time.time() - t_yolo) * 1000

        if processed_small is None or not isinstance(processed_small, np.ndarray):
            processed_small = frame_small.copy()

        # ─── Latencias ────────────────────────
        latencia_total = (time.time() - t_captura) * 1000
        overhead_ms    = latencia_total - yolo_ms
        fps            = 1000 / latencia_total if latencia_total > 0 else 0
        fps_list.append(fps)

        # ─── CSV ──────────────────────────────
        csv_writer.writerow([
            frame_count,
            datetime.now().strftime("%H:%M:%S.%f")[:-3],
            round(fps, 2),
            round(latencia_total, 2),
            round(yolo_ms, 2),
            round(overhead_ms, 2),
            inference_ms,
            cpu_percent,
            round(gpu_percent, 1),
            ram_percent,
            round(temp, 1),
            counter.in_count,
            counter.out_count,
            str(counter.classwise_counts)
        ])

        # ─── Métricas en tiempo real ──────
        if frame_count % 5 == 0:
            metrics = {
                'fps': round(fps, 1),
                'lat_total_ms': round(latencia_total, 1),
                'lat_inference_ms': inference_ms if inference_ms != '' else None,
                'gpu_pct': round(gpu_percent, 1),
                'cpu_pct': cpu_percent,
                'temp_c': round(temp, 1),
                'in_count': counter.in_count,
                'out_count': counter.out_count,
                'classwise': counter.classwise_counts,
                'frames': frame_count,
                'running': True
            }
            with open('/tmp/lab_metrics.json', 'w') as mf:
                json.dump(metrics, mf)

        # Log detecciones nuevas
        if counter.in_count != last_in_count:
            print(f"📊 Frame {frame_count} | in={counter.in_count} | "
                  f"clases={counter.classwise_counts}")
            last_in_count = counter.in_count

        # ─── Frame al stream ──────────────────
        frame_out = cv2.resize(processed_small, (WIDTH, HEIGHT))
        try:
            frame_queue.put_nowait(frame_out)
        except queue.Full:
            frames_dropped += 1

except KeyboardInterrupt:
    print("\n⏹ Deteniendo...")

finally:
    frame_queue.put(None)
    writer_thread.join(timeout=3)

    csv_file.close()
    cap.release()
    ffmpeg.stdin.close()
    ffmpeg.wait()

    avg_fps  = sum(fps_list) / len(fps_list) if fps_list else 0
    avg_temp = sum(temp_list) / len(temp_list) if temp_list else 0
    error_conteo = (
        abs(GROUND_TRUTH - counter.in_count) / GROUND_TRUTH * 100
        if GROUND_TRUTH > 0 else 0
    )
    avg_inference = (
        sum(inference_samples) / len(inference_samples)
        if inference_samples else 0
    )

    print(f"\n{'='*50}")
    print(f"=== RESULTADOS FINALES ===")
    print(f"{'='*50}")
    print(f"Frames procesados:    {frame_count}")
    print(f"Frames stream drop:   {frames_dropped} "
          f"({frames_dropped/frame_count*100:.1f}%)" if frame_count else "")
    print(f"FPS promedio:         {avg_fps:.1f}")
    print(f"Latencia total:       {1000/avg_fps:.1f} ms" if avg_fps else "")
    if inference_samples:
        print(f"Inferencia pura:      {avg_inference:.1f} ms "
              f"({len(inference_samples)} muestras)")
        print(f"Overhead estimado:    {1000/avg_fps - avg_inference:.1f} ms" if avg_fps else "")
    print(f"Temperatura promedio: {avg_temp:.1f}°C")
    print(f"")
    print(f"Total IN detectados:  {counter.in_count}")
    print(f"Ground truth:         {GROUND_TRUTH}")
    print(f"Error de conteo:      {error_conteo:.1f}%")
    print(f"Por clase:            {counter.classwise_counts}")
    print(f"")
    print(f"CSV guardado en:      {csv_filename}")
    print(f"{'='*50}")
