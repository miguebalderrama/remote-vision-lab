# Remote Vision Lab

> Laboratorio remoto de Edge AI para detección, clasificación y tracking de objetos en tiempo real en escenarios industriales. Construido sobre NVIDIA Jetson Orin Nano con modelos YOLO optimizados con TensorRT, diseñado para acceso remoto de estudiantes e investigadores.

![Remote Vision Lab — setup físico](docs/images/setup-overview.jpg)

*Cámara industrial sobre cinta transportadora detectando latas de conservas en tiempo real. Las detecciones, el tracking y la telemetría en vivo son accesibles vía dashboard web.*

**Estado:** 🚧 En desarrollo activo — benchmark completo en progreso.

🇬🇧 [Read in English](README.md)

---

## Dashboard en vivo

![Dashboard en vivo con detección en tiempo real](docs/images/dashboard-live.jpg)

*Inferencia en tiempo real con **YOLOv11s + TensorRT FP16** sobre Jetson Orin Nano. Métricas en vivo: FPS, latencia, uso de GPU, conteo por clase y variables del entorno físico.*

---

## Descripción general

`remote-vision-lab` es un laboratorio de Edge AI de bajo costo y replicable, que permite ejecutar experimentos de Computer Vision en tiempo real accesibles vía web. El sistema fue diseñado para que estudiantes e investigadores puedan entrenar, evaluar y poner a prueba modelos de detección de objetos en condiciones industriales reales — incluyendo perturbaciones visuales controladas y telemetría eléctrica en vivo.

El costo total del hardware ronda los **USD 500**, lo que vuelve al laboratorio accesible para universidades, escuelas técnicas y PyMEs que no pueden justificar sistemas de visión industrial de USD 10.000 o más.

**Financiado por Fundación YPF.** Desarrollado en el Laboratorio de Ingeniería de la **Universidad Nacional de General Sarmiento (UNGS)**, en el marco de **CONFEDI R-Lab** (Red Argentina Colaborativa de Laboratorios de Acceso Remoto).

---

## Características principales

- **Detección y tracking en tiempo real** con benchmarking comparativo entre YOLOv8 y YOLOv11.
- **Despliegue en edge** sobre NVIDIA Jetson Orin Nano 8GB (67 TOPS), con optimización TensorRT FP16.
- **Acceso remoto** de estudiantes mediante interfaz web (stream de video WebRTC + comandos WebSocket).
- **Control de hardware distribuido** vía ESP32 sobre WiFi/WebSocket (motores, sensores, iluminación, servo de oclusión).
- **Telemetría eléctrica** desde un sistema con UPS, que habilita estudios de correlación entre calidad de la red eléctrica y rendimiento del modelo.
- **Replicable y abierto** — stack completo de hardware y software documentado para que otras instituciones puedan adoptarlo.

---

## Arquitectura del sistema

El sistema sigue una arquitectura de dos capas: el **Jetson Orin Nano** centraliza los servicios de Computer Vision, backend y frontend, mientras que una **ESP32** maneja el control de hardware en tiempo real. Una **UPS Lyonn CTB-1200AP** brinda resiliencia eléctrica y telemetría.

```
[Navegador del estudiante] ──WebRTC/WebSocket──> [Jetson Orin Nano]
                                                       │
                                                       ├── YOLO + TensorRT (inferencia)
                                                       ├── BoT-SORT / ByteTrack (tracking)
                                                       ├── MediaMTX (streaming WebRTC)
                                                       ├── FastAPI + WebSocket (backend)
                                                       ├── Nginx (frontend)
                                                       └── NUT (telemetría UPS por USB)
                                                       │
                                          WiFi/WebSocket │
                                                       ↓
                                                    [ESP32]
                                                       │
       ┌──────────────────┬───────────────────┼──────────────────┐
       │                  │                   │                  │
   Sensores I2C       Barrera IR/GPIO     Servo PWM         Salida 0-10V
   (lux, temp,        + encoder          + LEDs             (variador motor)
    humedad)
```

Ver [`docs/architecture.pdf`](docs/architecture.pdf) para el documento arquitectónico completo.

---

## Hardware

| Componente | Función | Costo aprox. (USD) |
|---|---|---|
| Yahboom Jetson Orin Nano Super 8GB | Inferencia edge + backend + frontend | 250 |
| ESP32 DevKit | Control de hardware en tiempo real | 10 |
| UPS Lyonn CTB-1200AP (1200 VA) | Respaldo eléctrico + telemetría | 150 |
| Cámara industrial USB3.0 20 MP, lente varifocal | Adquisición de imagen | 80 |
| Sensores (BH1750, BME280), servo, barrera IR, encoder | Instrumentación de campo | ~30 |
| **Total** | | **~ 500** |

---

## Stack de software

| Capa | Tecnologías |
|---|---|
| **Inferencia** | PyTorch, Ultralytics, TensorRT 10.7 (FP16), CUDA 12.6, cuDNN 9.6 |
| **Tracking** | BoT-SORT, ByteTrack (evaluación comparativa) |
| **Streaming** | MediaMTX (WebRTC), FFmpeg |
| **Backend** | FastAPI (Python 3.10), WebSocket, Nginx |
| **Persistencia** | _A definir_ |
| **Monitoreo UPS** | NUT (Network UPS Tools) |
| **SO** | Ubuntu 22.04 (JetPack R36.4.3) |
| **Microcontrolador** | ESP32 (framework Arduino), cliente WebSocket, I2C, GPIO, PWM, salida 0-10V |

---

## Modelos en evaluación

El laboratorio compara cuatro modelos de detección de objetos, sobre dos backends de ejecución (PyTorch puro vs. TensorRT FP16):

| Modelo | Tamaño | Backends |
|---|---|---|
| YOLOv8s | small | PyTorch, TensorRT FP16 |
| YOLOv8m | medium | PyTorch, TensorRT FP16 |
| YOLOv11s | small | PyTorch, TensorRT FP16 |
| YOLOv11m | medium | PyTorch, TensorRT FP16 |

También se comparan dos algoritmos de tracking sobre cada detector:

- **BoT-SORT**
- **ByteTrack**

### Dataset

Dataset propio curado para detección de latas de conservas:

- **Clases:** 3 — `picadillo`, `foie`, `picante`
- **Total de imágenes:** 1.200
- **Split:** 1.050 train / 100 validación / 50 test
- **Preprocesamiento:** auto-orient, resize-fit a 640×640 (relleno negro)
- **Aumentos (pipeline Roboflow):** flip horizontal/vertical, rotación ±15°, 15% en escala de grises, saturación ±25%, brillo ±15%, blur hasta 2px, ruido hasta 0,22%. 3 salidas por imagen.

### Resultados preliminares

| Modelo | Backend | mAP@0.5 | FPS | Latencia end-to-end |
|---|---|---|---|---|
| YOLOv8s | PyTorch | _A completar_ | _A completar_ | _A completar_ |
| YOLOv8s | TensorRT FP16 | _A completar_ | _A completar_ | _A completar_ |
| YOLOv8m | PyTorch | _A completar_ | _A completar_ | _A completar_ |
| YOLOv8m | TensorRT FP16 | _A completar_ | _A completar_ | _A completar_ |
| YOLOv11s | PyTorch | _A completar_ | _A completar_ | _A completar_ |
| **YOLOv11s** | **TensorRT FP16** | _A completar_ | **47.2** | **56.5 ms** |
| YOLOv11m | PyTorch | _A completar_ | _A completar_ | _A completar_ |
| YOLOv11m | TensorRT FP16 | _A completar_ | _A completar_ | _A completar_ |

> Primera corrida validada: **YOLOv11s + TensorRT FP16 → 47,2 FPS sostenidos a 56,5 ms de latencia end-to-end**, GPU al 78%, temperatura del SoC 55°C. Benchmark completo entre todas las combinaciones modelo/backend en progreso.

---

## Estructura del repositorio

```
remote-vision-lab/
├── README.md                  # Versión en inglés
├── README.es.md               # Este archivo (español)
├── docs/
│   ├── architecture.pdf       # Documento arquitectónico completo
│   └── images/                # Capturas del proyecto
├── jetson/
│   ├── inference/             # Pipeline YOLO + TensorRT
│   ├── tracking/              # Integración BoT-SORT / ByteTrack
│   ├── backend/               # FastAPI + WebSocket
│   ├── streaming/             # Configuración MediaMTX
│   └── ups/                   # Integración telemetría NUT
├── esp32/
│   ├── firmware/              # Código Arduino para ESP32
│   └── docs/                  # Cableado de sensores/actuadores
├── dataset/                   # Imágenes de muestra y metadatos (set completo en Roboflow)
├── frontend/                  # Interfaz web (HTML5 + WebRTC)
└── notebooks/                 # Notebooks de entrenamiento y benchmarking
```

---

## Cómo empezar

> Las instrucciones de instalación se agregarán al finalizar la fase de validación.

---

## Roadmap

- [x] Arquitectura de hardware definida y documentada
- [x] Dataset propio curado (1.200 imágenes, 3 clases)
- [x] Primera corrida validada (YOLOv11s + TensorRT FP16 → 47,2 FPS)
- [ ] Entrenamiento de las variantes YOLOv8 / YOLOv11 restantes
- [ ] Benchmarking TensorRT FP16 completo en todas las variantes
- [ ] Evaluación comparativa BoT-SORT vs ByteTrack
- [ ] Validación de métricas end-to-end
- [ ] Interfaz web pública para estudiantes remotos
- [ ] Experimentos de robustez adversarial (oclusión + iluminación)
- [ ] Análisis de correlación: telemetría eléctrica ↔ rendimiento del modelo

---

## Cita

Si usás este proyecto en trabajos académicos, citalo como:

```bibtex
@misc{balderrama2026remotevisionlab,
  author = {Balderrama, Miguel Angel},
  title  = {Remote Vision Lab: laboratorio de Edge AI para Computer Vision industrial},
  year   = {2026},
  institution = {Universidad Nacional de General Sarmiento},
  note   = {Financiado por Fundación YPF, en el marco de CONFEDI R-Lab}
}
```

---

## Autor

**Miguel Angel Balderrama**
Computer Vision & Machine Learning Engineer | Laboratorio de Ingeniería, UNGS
📧 miguel.balderr@gmail.com
🔗 [linkedin.com/in/mbalderr-dev](https://www.linkedin.com/in/mbalderr-dev)
🔗 [github.com/miguebalderrama](https://github.com/miguebalderrama)

---

## Agradecimientos

- **Fundación YPF** — Financiamiento del proyecto.
- **CONFEDI R-Lab** — Marco institucional.
- **Universidad Nacional de General Sarmiento (UNGS)** — Institución sede.

---

## Licencia

Licencia MIT — ver [LICENSE](LICENSE) para detalles.
