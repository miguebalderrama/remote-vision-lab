"""
control_api.py — Jetson Orin Nano
Recibe comandos del dashboard HTML y gestiona el proceso de benchmark.
Lanzar con: uvicorn control_api:app --host 0.0.0.0 --port 8765
"""

import subprocess
import os
import signal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Lab Remoto CV · Control API")

# CORS — permite que el HTML desde file:// o localhost se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Modelos disponibles ───────────────────────
MODELOS = {
    "y11s_engine": "/home/jetson/yolo11s.engine",
    "y11m_engine": "/home/jetson/yolo11m.engine",
    "y8s_engine":  "/home/jetson/yolov8s.engine",
    "y8m_engine":  "/home/jetson/yolov8m.engine",
    "y11s_pt":     "/home/jetson/yolo11s.pt",
    "y11m_pt":     "/home/jetson/yolo11m.pt",
    "y8s_pt":      "/home/jetson/yolov8s.pt",
    "y8m_pt":      "/home/jetson/yolov8m.pt",
}

# ── Estado ────────────────────────────────────
estado = {
    "proceso":       None,   # Popen del benchmark
    "modelo_actual": None,
    "corriendo":     False,
}

# ── Schemas ───────────────────────────────────
class ComandoModelo(BaseModel):
    modelo: str   # clave de MODELOS

class ComandoStop(BaseModel):
    pass

# ── Helpers ───────────────────────────────────
def matar_proceso():
    p = estado["proceso"]
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    estado["proceso"]  = None
    estado["corriendo"] = False

def lanzar_benchmark(model_path: str):
    matar_proceso()
    env = os.environ.copy()
    env["MODEL_PATH"] = model_path
    env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/cuda/bin"
    p = subprocess.Popen(
        ["python3", "/home/jetson/benchmark_v6.py"],
        env=env,
        stdout=open("/tmp/benchmark_out.log", "w"),
        stderr=open("/tmp/benchmark_err.log", "w"),
        close_fds=True,
        start_new_session=True
    )
    estado["proceso"]       = p
    estado["modelo_actual"] = model_path
    estado["corriendo"]     = True
    return p.pid

# ── Endpoints ─────────────────────────────────

@app.get("/")
def root():
    return {"msg": "Lab Remoto CV · Control API", "docs": "/docs"}

@app.get("/estado")
def get_estado():
    p = estado["proceso"]
    corriendo = p is not None and p.poll() is None
    estado["corriendo"] = corriendo
    return {
        "corriendo":     corriendo,
        "modelo_actual": estado["modelo_actual"],
        "modelos":       list(MODELOS.keys()),
    }

@app.post("/iniciar")
def iniciar(cmd: ComandoModelo):
    if cmd.modelo not in MODELOS:
        return {"error": f"Modelo '{cmd.modelo}' no válido. Opciones: {list(MODELOS.keys())}"}
    pid = lanzar_benchmark(MODELOS[cmd.modelo])
    return {
        "ok":    True,
        "modelo": cmd.modelo,
        "path":  MODELOS[cmd.modelo],
        "pid":   pid,
    }

@app.get("/metricas")
def metricas():
    import json, os
    path = '/tmp/lab_metrics.json'
    if not os.path.exists(path):
        return {'running': False}
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {'running': False}

@app.post("/detener")
def detener():
    matar_proceso()
    return {"ok": True, "msg": "Benchmark detenido"}
