# Remote Vision Lab

> Laboratorio de Edge AI para detección, clasificación y seguimiento de objetos en tiempo real en escenarios industriales. Construido sobre NVIDIA Jetson Orin Nano con modelos YOLO optimizados con TensorRT, diseñado para acceso remoto de estudiantes e investigadores.

<p align="center">
  <img src="docs/images/setup-overview.jpg" alt="Remote Vision Lab — setup físico" width="640">
</p>

*Cámara industrial sobre una cinta transportadora detectando productos enlatados en tiempo real. Las detecciones, el tracking y la telemetría en vivo son accesibles desde un dashboard web.*

**Estado:** 🚧 En desarrollo activo — automatización de la cinta en progreso.

🇬🇧 [Read in English](README.md)

---

## Dashboard en vivo

<p align="center">
  <img src="docs/images/dashboard-live.webp" alt="Dashboard en vivo con detección en tiempo real" width="640">
</p>

*Inferencia en tiempo real con **YOLOv11s + TensorRT FP16** sobre Jetson Orin Nano. Métricas en vivo: FPS, latencia, uso de GPU, conteo por clase y variables del entorno físico.*

---

## Descripción general

`remote-vision-lab` es un laboratorio de Edge AI de bajo costo y replicable que ejecuta experimentos de Visión Artificial en tiempo real accesibles desde la web. El sistema fue diseñado para que estudiantes e investigadores entrenen, evalúen y pongan a prueba modelos de detección de objetos en condiciones industriales reales — incluyendo perturbaciones visuales controladas y telemetría eléctrica en vivo.

El costo total del hardware es de aproximadamente **USD 535**, lo que hace al laboratorio accesible para universidades, escuelas técnicas y PyMEs que no pueden justificar sistemas de visión industrial de rango USD 10.000+.

**Financiado por la Fundación YPF.** Desarrollado en el Laboratorio de Ingeniería de la **Universidad Nacional de General Sarmiento (UNGS)**, en el marco de **CONFEDI R-Lab** (Red Argentina de Laboratorios de Acceso Remoto Colaborativos).

---

## Características principales

- **Detección y seguimiento de objetos en tiempo real** con benchmarking comparativo entre YOLOv8 y YOLOv11.
- **Despliegue en edge** sobre NVIDIA Jetson Orin Nano 8GB (67 TOPS), con optimización TensorRT FP16.
- **Acceso remoto** para estudiantes a través de una interfaz web (streaming de video WebRTC + comandos REST).
- **Streaming de audio en vivo** desde el entorno del laboratorio vía WebRTC (codec Opus).
- **Control de hardware distribuido** vía ESP32 por WiFi/WebSocket (motores, sensores, iluminación).
- **Telemetría eléctrica** desde un sistema protegido por UPS.
- **Replicable y abierto** — todo el stack de hardware y software documentado para adopción por otras instituciones.

---

## Arquitectura del sistema

El sistema sigue una arquitectura de dos capas: la **Jetson Orin Nano** centraliza los servicios de Visión Artificial, backend y frontend, mientras que un **ESP32** gestiona el control de hardware en tiempo real.

```
[Navegador del alumno] ──WebRTC/REST──> [Jetson Orin Nano]
                                               │
                                               ├── YOLO + TensorRT (inferencia + tracking + métricas)
                                               ├── MediaMTX (streaming WebRTC — video + audio)
                                               ├── FastAPI (API REST — control de modelos + métricas)
                                               ├── Dashboard web (HTML5 + WebRTC + Canvas)
                                               └── systemd (arranque automático al encender)
                                               │
                                   WiFi/WebSocket │
                                               ↓
                                           [ESP32]
                                               │
       ┌──────────────────┬───────────────────┴──────────────────┐
       │                  │                                       │
   Sensores I2C      Barrera IR + encoder                  PWM + salida 0-10V
   (lux, temp)                                            (velocidad motor + iluminación)
```

Ver [`docs/architecture.pdf`](docs/architecture.pdf) para el documento de arquitectura completo.

---

## Hardware

| Componente | Función | Costo aprox. (USD) |
|---|---|---|
| Yahboom Jetson Orin Nano Super 8GB | Inferencia edge + backend + frontend | 250 |
| ESP32 DevKit | Control de hardware en tiempo real | 10 |
| UPS Lyonn CTB-1200AP (1200 VA) | Respaldo eléctrico + telemetría | 150 |
| Cámara USB industrial (ELP USB4KCam) | Adquisición de imágenes — vista superior sobre la cinta | 80 |
| Micrófono USB BY-PM300 | Streaming de audio en vivo desde el laboratorio | ~15 |
| Sensores, servo, barrera IR, encoder | Instrumentación de campo | ~30 |
| **Total** | | **~ 535** |

---

## Stack de software

| Capa | Tecnologías |
|---|---|
| **Inferencia + Tracking** | PyTorch, Ultralytics, TensorRT 10.7 (FP16), CUDA 12.6, BoT-SORT |
| **Streaming** | MediaMTX v1.9.1 (WebRTC/WHEP), FFmpeg (H.264 + Opus) |
| **Backend** | FastAPI (Python 3.10), uvicorn |
| **Frontend** | HTML5, WebRTC, Canvas (sparkline), JS vanilla |
| **Gestión de procesos** | systemd (arranque automático + reinicio ante fallos) |
| **SO** | Ubuntu 22.04 (JetPack R36.4.3) |
| **Microcontrolador** | ESP32 (Arduino framework), WebSocket, I2C, GPIO, PWM |

---

## Modelos bajo evaluación

El laboratorio realiza benchmarks de cuatro arquitecturas de detección de objetos en dos backends de ejecución (PyTorch vs. TensorRT FP16):

| Modelo | Tamaño | Backends |
|---|---|---|
| YOLOv8s | pequeño | PyTorch, TensorRT FP16 |
| YOLOv8m | mediano | PyTorch, TensorRT FP16 |
| YOLOv11s | pequeño | PyTorch, TensorRT FP16 |
| YOLOv11m | mediano | PyTorch, TensorRT FP16 |

### Dataset

Dataset personalizado para detección de alimentos enlatados en un entorno de cinta transportadora industrial:

- **Clases:** 3 — `picadillo`, `foie`, `picante`
- **Total de imágenes:** 1.200
- **Split:** 1.050 entrenamiento / 100 validación / 50 test
- **Capturado in-situ** sobre el hardware objetivo, replicando las condiciones reales de inferencia
- **Preprocesamiento:** Auto-orientación, redimensionado a 640×640 (relleno negro)
- **Aumentaciones (pipeline Roboflow):** ±15° rotación, 15% escala de grises, ±25% saturación, ±15% brillo, hasta 2px de blur, hasta 0.22% de ruido. 3 salidas por ejemplo de entrenamiento.
- **Protocolo de entrenamiento:** Las cuatro arquitecturas fueron entrenadas con el mismo dataset y el mismo protocolo, garantizando que las diferencias en la evaluación reflejen la arquitectura y no las condiciones de entrenamiento.

### Resultados de benchmark — Línea base estática

> **Nota:** Estos resultados representan el rendimiento sostenido sobre la Jetson Orin Nano 8GB **sin objetos en la cinta transportadora** (línea base estática). Las métricas de precisión (mAP@0.5) se evaluarán bajo condiciones operativas dinámicas una vez completada la automatización de la cinta.

| Modelo | Backend | FPS | Latencia total | Inferencia pura | Overhead pipeline | Temp prom |
|---|---|---|---|---|---|---|
| YOLOv8s | TensorRT FP16 | **18,4** | **54,4 ms** | 27,8 ms | 26,6 ms | 45,9°C |
| YOLOv11s | TensorRT FP16 | 17,7 | 56,4 ms | 28,2 ms | 28,2 ms | 44,9°C |
| YOLOv8s | PyTorch | 17,7 | 56,6 ms | 36,4 ms | 20,3 ms | 51,8°C |
| YOLOv11s | PyTorch | 17,4 | 57,4 ms | 37,6 ms | 19,9 ms | 47,7°C |
| YOLOv11m | PyTorch | 15,8 | 63,5 ms | 44,5 ms | 19,0 ms | 54,2°C |
| YOLOv8m | PyTorch | 15,8 | 63,2 ms | 43,9 ms | 19,2 ms | 57,5°C |
| YOLOv11m | TensorRT FP16 | 14,0 | 71,6 ms | 40,3 ms | 31,4 ms | 46,7°C |
| YOLOv8m | TensorRT FP16 | 13,5 | 73,9 ms | 42,8 ms | 31,1 ms | 46,4°C |

### Hallazgos principales

**TensorRT reduce la latencia de inferencia pero no mejora el FPS end-to-end.**
TensorRT FP16 reduce el tiempo de inferencia pura un ~25% (ej: YOLOv11s: 37,6 ms → 28,2 ms). Sin embargo, el FPS total es casi idéntico al de PyTorch porque TRT incrementa el overhead del pipeline (~28 ms vs ~20 ms en PyTorch). El perfil indica que el overhead se origina en las transferencias de memoria GPU↔CPU y la etapa de encoding con FFmpeg — áreas que TensorRT no optimiza.

**La ventaja real de TensorRT es la eficiencia térmica.**
A pesar del FPS similar, TensorRT FP16 logra hasta **11°C menos de temperatura del SoC** respecto a PyTorch con el mismo modelo (YOLOv8m: 46,4°C vs 57,5°C). Para operación industrial continua 24/7, esto se traduce directamente en menor estrés térmico y mayor vida útil del hardware.

**El overhead del pipeline domina en los modelos TRT.**
En TensorRT, el overhead del pipeline representa ~50% de la latencia total (inferencia ≈ overhead). En PyTorch, la inferencia domina (~65-70%). Esto significa que para despliegues TRT, optimizar el modelo tiene rendimientos decrecientes — el cuello de botella se desplazó al pipeline circundante (captura → resize → tracking → encoding).

**La arquitectura (v8 vs v11) importa menos que el tamaño del modelo (s vs m).**
Dentro de la misma clase de tamaño, YOLOv8 y YOLOv11 entregan FPS y latencia casi idénticos. El factor dominante es el tamaño: las variantes `m` son ~25% más lentas y corren entre 5-11°C más calientes que las variantes `s`.

**Modelo recomendado para producción continua:** `YOLOv8s TensorRT FP16` — mayor FPS (18,4), menor latencia (54,4 ms), temperatura más baja entre los modelos TRT (45,9°C).

---

## Estructura del repositorio

```
remote-vision-lab/
├── README.md                  # Versión en inglés
├── README.es.md               # Este archivo (español)
├── docs/
│   ├── architecture.pdf       # Documento de arquitectura completo
│   └── images/                # Capturas y fotos del setup
├── jetson/
│   ├── vision/                # Pipeline de inferencia (YOLO + TensorRT + tracking + métricas)
│   ├── backend/               # API REST FastAPI
│   ├── streaming/             # Configuración MediaMTX
│   ├── frontend/              # Dashboard web (HTML5 + WebRTC)
│   └── systemd/               # Unidades de servicio systemd
├── esp32/
│   ├── firmware/              # Código Arduino para ESP32
│   └── docs/                  # Diagramas de cableado de sensores/actuadores
├── experiments/               # CSVs de benchmarks y resultados
└── dataset/                   # Imágenes de muestra y metadatos (set completo en Roboflow)
```

---

## Inicio rápido

> Las instrucciones completas de instalación se publicarán cuando finalice la fase de validación.
> Inicio rápido actual para el stack de streaming + inferencia:

```bash
# 1. Arrancar MediaMTX + audio (corre como servicio systemd al encender)
./start_lab.sh

# 2. Arrancar API de control (corre como servicio systemd al encender)
uvicorn control_api:app --host 0.0.0.0 --port 8765

# 3. Abrir dashboard
http://<ip-jetson>:8080/lab_v5_spark.html
```

---

## Roadmap

- [x] Arquitectura de hardware definida y documentada
- [x] Dataset personalizado curado (1.200 imágenes, 3 clases, capturado in-situ)
- [x] Las 8 variantes de modelos entrenadas (YOLOv8/v11 × s/m × PyTorch/TensorRT FP16)
- [x] Streaming WebRTC de doble cámara operativo (detección + overview)
- [x] Streaming de audio en vivo vía WebRTC (codec Opus, micrófono BY-PM300)
- [x] Selección de modelo y lanzamiento de experimentos desde el dashboard web
- [x] Pipeline de métricas en tiempo real (FPS, latencia, GPU%, temperatura) vía REST API
- [x] Benchmark estático completo con TensorRT FP16 en todas las variantes de modelos
- [x] Arranque automático con systemd para todos los servicios
- [ ] Integración de automatización de la cinta transportadora (ESP32 + control de motor)
- [ ] Benchmark dinámico con conteo de objetos contra ground truth
- [ ] Evaluación comparativa BoT-SORT vs ByteTrack
- [ ] Evaluación de mAP bajo condiciones operativas
- [ ] Historial de experimentos SQLite para sesiones de alumnos
- [ ] Interfaz web pública para alumnos remotos

---

## Cita

Si utilizás este proyecto en trabajos académicos, por favor citar:

```bibtex
@misc{balderrama2026remotevisionlab,
  author      = {Balderrama, Miguel Angel},
  title       = {Remote Vision Lab: an Edge AI laboratory for industrial Computer Vision},
  year        = {2026},
  institution = {Universidad Nacional de General Sarmiento},
  note        = {Funded by Fundación YPF, in the framework of CONFEDI R-Lab}
}
```

---

## Autor

**Miguel Angel Balderrama**
Ingeniero en Visión Artificial y Machine Learning | Laboratorio de Ingeniería, UNGS
📧 miguel.balderr@gmail.com
🔗 [linkedin.com/in/mbalderr-dev](https://www.linkedin.com/in/mbalderr-dev)
🔗 [github.com/miguebalderrama](https://github.com/miguebalderrama)

---

## Agradecimientos

- **CONFEDI R-Lab** — Marco institucional.
- **Universidad Nacional de General Sarmiento (UNGS)** — Institución anfitriona.
- **Fundación YPF** — Financiamiento.

---

## Licencia

Licencia MIT — ver [LICENSE](LICENSE) para más detalles.