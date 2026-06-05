# Remote Vision Lab

> Edge AI laboratory for real-time object detection, classification and tracking on industrial scenarios. Built around NVIDIA Jetson Orin Nano with TensorRT-optimized YOLO models, designed for remote access by students and researchers.

<p align="center">
  <img src="docs/images/setup-overview.jpg" alt="Remote Vision Lab — physical setup" width="640">
</p>

*Industrial camera over a conveyor belt detecting canned food products in real time. Detections, tracking, and live telemetry are accessible via a web dashboard.*

**Status:** 🚧 Under active development — conveyor belt automation in progress.

🇪🇸 [Leer en español](README.es.md)

---

## Live Dashboard

<p align="center">
  <img src="docs/images/dashboard-live.webp" alt="Live dashboard with real-time detection" width="640">
</p>

*Real-time inference with **YOLOv11s + TensorRT FP16** on Jetson Orin Nano. Live metrics: FPS, latency, GPU usage, per-class counting, and physical environment variables.*

---

## Overview

`remote-vision-lab` is a low-cost, replicable Edge AI laboratory that runs real-time Computer Vision experiments accessible over the web. The system was designed to let students and researchers train, evaluate and stress-test object detection models on real industrial conditions — including controlled visual disturbances and live electrical telemetry.

The full hardware bill of materials is approximately **USD 500**, making the lab affordable for universities, technical schools and SMEs that cannot justify industrial vision systems in the USD 10,000+ range.

**Funded by Fundación YPF.** Developed at the Engineering Laboratory of **Universidad Nacional de General Sarmiento (UNGS)**, in the framework of **CONFEDI R-Lab** (Argentine Collaborative Network of Remote Access Laboratories).

---

## Key Features

- **Real-time object detection and tracking** with comparative benchmarking between YOLOv8 and YOLOv11.
- **Edge deployment** on NVIDIA Jetson Orin Nano 8GB (67 TOPS), with TensorRT FP16 optimization.
- **Remote access** for students through a web interface (WebRTC video stream + REST API commands).
- **Live audio streaming** from the laboratory environment via WebRTC (Opus codec).
- **Distributed hardware control** via ESP32 over WiFi/WebSocket (motors, sensors, lighting).
- **Electrical telemetry** from a UPS-protected system.
- **Replicable and open** — full hardware and software stack documented for adoption by other institutions.

---

## System Architecture

The system follows a two-layer architecture: the **Jetson Orin Nano** centralizes Computer Vision, backend and frontend services, while an **ESP32** handles real-time hardware control.

```
[Student Browser] ──WebRTC/REST──> [Jetson Orin Nano]
                                          │
                                          ├── YOLO + TensorRT (inference + tracking + metrics)
                                          ├── MediaMTX (WebRTC streaming — video + audio)
                                          ├── FastAPI (REST backend — model control + metrics)
                                          ├── Web dashboard (HTML5 + WebRTC + Canvas)
                                          └── systemd (auto-start on boot)
                                          │
                              WiFi/WebSocket │
                                          ↓
                                      [ESP32]
                                          │
       ┌──────────────────┬──────────────┴──────────────────┐
       │                  │                                  │
   I2C sensors       GPIO/IR barrier                   PWM + 0-10V drive
   (lux, temp)       + encoder                         (motor speed + lighting)
```

See [`docs/architecture.pdf`](docs/architecture.pdf) for the full architectural document.

---

## Hardware

| Component | Role | Approx. cost (USD) |
|---|---|---|
| Yahboom Jetson Orin Nano Super 8GB | Edge inference + backend + frontend | 250 |
| ESP32 DevKit | Real-time hardware control | 10 |
| UPS Lyonn CTB-1200AP (1200 VA) | Power backup + electrical telemetry | 150 |
| Industrial USB camera (ELP USB4KCam) | Image acquisition — top-view over belt | 80 |
| BY-PM300 USB microphone | Live audio streaming from lab | ~15 |
| Sensors, servo, IR barrier, encoder | Field-layer instrumentation | ~30 |
| **Total** | | **~ 535** |

---

## Software Stack

| Layer | Technologies |
|---|---|
| **Inference + Tracking** | PyTorch, Ultralytics, TensorRT 10.7 (FP16), CUDA 12.6, BoT-SORT |
| **Streaming** | MediaMTX v1.9.1 (WebRTC/WHEP), FFmpeg (H.264 + Opus) |
| **Backend** | FastAPI (Python 3.10), uvicorn |
| **Frontend** | HTML5, WebRTC, Canvas (sparkline), vanilla JS |
| **Process management** | systemd (auto-start + restart on failure) |
| **OS** | Ubuntu 22.04 (JetPack R36.4.3) |
| **Microcontroller** | ESP32 (Arduino framework), WebSocket, I2C, GPIO, PWM |

---

## Models Under Evaluation

The lab benchmarks four object detection architectures across two execution backends (PyTorch vs. TensorRT FP16):

| Model | Size | Backends |
|---|---|---|
| YOLOv8s | small | PyTorch, TensorRT FP16 |
| YOLOv8m | medium | PyTorch, TensorRT FP16 |
| YOLOv11s | small | PyTorch, TensorRT FP16 |
| YOLOv11m | medium | PyTorch, TensorRT FP16 |

### Dataset

Custom-curated dataset for canned food detection in an industrial conveyor environment:

- **Classes:** 3 — `picadillo`, `foie`, `picante`
- **Total images:** 1,200
- **Split:** 1,050 train / 100 validation / 50 test
- **Captured on-site** on the target hardware, replicating real inference conditions
- **Preprocessing:** Auto-orient, resize-fit to 640×640 (black padding)
- **Augmentations (Roboflow pipeline):** ±15° rotation, 15% grayscale, ±25% saturation, ±15% brightness, up to 2px blur, up to 0.22% noise. 3 outputs per training example.
- **Training protocol:** All four architectures trained with the same dataset and training protocol, ensuring differences in evaluation reflect architecture choices rather than training conditions.

### Benchmark Results — Static Baseline

> **Note:** These results represent sustained baseline performance on the Jetson Orin Nano 8GB **without objects on the conveyor belt** (static baseline). Accuracy metrics (mAP@0.5) will be evaluated under dynamic operational conditions once conveyor belt automation is complete.

| Model | Backend | FPS | End-to-end latency | Pure inference | Pipeline overhead | Avg temp |
|---|---|---|---|---|---|---|
| YOLOv8s | TensorRT FP16 | **18.4** | **54.4 ms** | 27.8 ms | 26.6 ms | 45.9°C |
| YOLOv11s | TensorRT FP16 | 17.7 | 56.4 ms | 28.2 ms | 28.2 ms | 44.9°C |
| YOLOv8s | PyTorch | 17.7 | 56.6 ms | 36.4 ms | 20.3 ms | 51.8°C |
| YOLOv11s | PyTorch | 17.4 | 57.4 ms | 37.6 ms | 19.9 ms | 47.7°C |
| YOLOv11m | PyTorch | 15.8 | 63.5 ms | 44.5 ms | 19.0 ms | 54.2°C |
| YOLOv8m | PyTorch | 15.8 | 63.2 ms | 43.9 ms | 19.2 ms | 57.5°C |
| YOLOv11m | TensorRT FP16 | 14.0 | 71.6 ms | 40.3 ms | 31.4 ms | 46.7°C |
| YOLOv8m | TensorRT FP16 | 13.5 | 73.9 ms | 42.8 ms | 31.1 ms | 46.4°C |

### Key Findings

**TensorRT reduces inference latency but not end-to-end FPS.**
TensorRT FP16 reduces pure inference time by ~25% (e.g., YOLOv11s: 37.6 ms → 28.2 ms). However, end-to-end FPS remains nearly identical to PyTorch because TRT increases pipeline overhead (~28 ms vs ~20 ms in PyTorch). Profiling suggests the overhead originates in GPU↔CPU memory transfers and the FFmpeg encoding stage — areas that TensorRT does not optimize.

**TensorRT's real advantage is thermal efficiency.**
Despite similar FPS, TensorRT FP16 yields up to **11°C lower SoC temperatures** compared to PyTorch on the same model (YOLOv8m: 46.4°C vs 57.5°C). For continuous 24/7 industrial operation, this translates directly to reduced thermal stress and longer hardware lifespan.

**Pipeline overhead dominates for TRT models.**
In TensorRT, pipeline overhead accounts for ~50% of total latency (inference ≈ overhead). In PyTorch, inference dominates (~65–70%). This means that for TRT deployments, optimizing the model further yields diminishing returns — the bottleneck has shifted to the surrounding pipeline (capture → resize → track → encode).

**Architecture (v8 vs v11) matters less than model size (s vs m).**
Within the same size class, YOLOv8 and YOLOv11 deliver nearly identical FPS and latency. The dominant factor is model size: `m` variants are ~25% slower and run 5–11°C hotter than `s` variants.

**Recommended model for continuous production use:** `YOLOv8s TensorRT FP16` — highest FPS (18.4), lowest latency (54.4 ms), lowest temperature among TRT models (45.9°C).

---

## Repository Structure

```
remote-vision-lab/
├── README.md                  # This file (English)
├── README.es.md               # Spanish version
├── docs/
│   ├── architecture.pdf       # Full system architecture document
│   └── images/                # Project screenshots and setup photos
├── jetson/
│   ├── vision/                # Inference pipeline (YOLO + TensorRT + tracking + metrics)
│   ├── backend/               # FastAPI REST API
│   ├── streaming/             # MediaMTX configuration
│   ├── frontend/              # Web dashboard (HTML5 + WebRTC)
│   └── systemd/               # systemd service units
├── esp32/
│   ├── firmware/              # Arduino code for ESP32
│   └── docs/                  # Sensor/actuator wiring diagrams
├── experiments/               # Benchmark CSVs and results
└── dataset/                   # Sample images and metadata (full set on Roboflow)
```

---

## Getting Started

> Full setup instructions will be published once the validation phase is complete.
> Current quick-start for the streaming + inference stack:

```bash
# 1. Start MediaMTX + audio (runs as systemd service on boot)
./start_lab.sh

# 2. Start control API (runs as systemd service on boot)
uvicorn control_api:app --host 0.0.0.0 --port 8765

# 3. Open dashboard
http://<jetson-ip>:8080/lab_v5_spark.html
```

---

## Roadmap

- [x] Hardware architecture defined and documented
- [x] Custom dataset curated (1,200 images, 3 classes, captured on-site)
- [x] All 8 model variants trained (YOLOv8/v11 × s/m × PyTorch/TensorRT FP16)
- [x] Dual camera WebRTC streaming operational (detection + overview)
- [x] Live audio streaming via WebRTC (Opus codec, BY-PM300 microphone)
- [x] Model selection and experiment launch via web dashboard
- [x] Real-time metrics pipeline (FPS, latency, GPU%, temperature) via REST API
- [x] Full TensorRT FP16 static benchmarking across all model variants
- [x] systemd auto-start for all services
- [ ] Conveyor belt automation integration (ESP32 + motor control)
- [ ] Dynamic benchmark with ground-truth object counting
- [ ] BoT-SORT vs ByteTrack comparative evaluation
- [ ] mAP evaluation under operational conditions
- [ ] SQLite experiment history for student sessions
- [ ] Public web interface for remote students

---

## Citation

If you use this project in academic work, please cite:

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

## Author

**Miguel Angel Balderrama**
Computer Vision & Machine Learning Engineer | Engineering Laboratory, UNGS
📧 miguel.balderr@gmail.com
🔗 [linkedin.com/in/mbalderr-dev](https://www.linkedin.com/in/mbalderr-dev)
🔗 [github.com/miguebalderrama](https://github.com/miguebalderrama)

---

## Acknowledgments

- **CONFEDI R-Lab** — Institutional framework.
- **Universidad Nacional de General Sarmiento (UNGS)** — Host institution.
- **Fundación YPF** — Funding.

---

## License

MIT License — see [LICENSE](LICENSE) for details.