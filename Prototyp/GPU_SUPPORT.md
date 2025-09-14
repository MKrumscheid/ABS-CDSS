# GPU Support für RAG Service

## Überblick

Der RAG Service unterstützt jetzt automatische GPU-Erkennung und kann auf verschiedenen Hardware-Konfigurationen laufen:

- **NVIDIA GPU** (CUDA) - Beste Performance für ML-Workloads
- **Apple Silicon** (MPS) - Optimiert für M1/M2/M3 Macs
- **Intel Integrated GPU** - Begrenzte Unterstützung über CPU-Fallback
- **CPU** - Funktioniert überall als Fallback

## Installation

### Automatisches Setup (Empfohlen)

```bash
# Windows
setup_gpu.bat

# Oder manuell:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Manuelle GPU-Installation

#### NVIDIA GPU (CUDA)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Apple Silicon

```bash
pip install torch torchvision torchaudio
```

#### CPU-only

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## Device Information API

Der Service bietet einen neuen Endpoint um Geräteinformationen abzurufen:

```bash
GET /device-info
```

Beispiel Response:

```json
{
  "status": "success",
  "device_info": {
    "device": "cuda",
    "device_name": "NVIDIA GeForce RTX 4080",
    "memory_gb": 16.0,
    "torch_available": true,
    "cuda_available": true,
    "mps_available": false
  }
}
```

## Hardware-spezifische Hinweise

### NVIDIA GPU

- **Unterstützt**: Alle modernen NVIDIA GPUs mit CUDA-Unterstützung
- **Performance**: Beste Performance für ML-Inferenz
- **Memory**: Benötigt mindestens 4GB VRAM für das multilingual-e5-large Modell

### Intel Iris (Integrierte GPU)

- **Eingeschränkte Unterstützung**: Intel GPUs werden normalerweise nicht direkt von PyTorch unterstützt
- **Fallback**: System nutzt automatisch CPU mit optimierter BLAS-Bibliothek
- **Alternative**: Intel Extension for PyTorch (experimentell)

```bash
# Experimentelle Intel GPU Unterstützung
pip install intel-extension-for-pytorch
```

### Apple Silicon (M1/M2/M3)

- **Unterstützt**: Alle Apple Silicon Macs
- **Performance**: Deutlich schneller als CPU-only
- **Memory**: Nutzt unified memory effizient

### AMD GPU

- **Experimentell**: ROCm-Unterstützung verfügbar

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.4.2
```

## Performance-Vergleich

| Hardware        | Relative Performance | Memory Usage |
| --------------- | -------------------- | ------------ |
| NVIDIA RTX 4080 | 100% (Baseline)      | 2-4 GB VRAM  |
| Apple M2 Pro    | ~60-80%              | 2-4 GB RAM   |
| Intel i7 CPU    | ~15-25%              | 4-8 GB RAM   |
| Intel Iris      | ~15-25%              | 4-8 GB RAM   |

## Troubleshooting

### GPU nicht erkannt

```bash
# Prüfe CUDA Installation
python -c "import torch; print(torch.cuda.is_available())"

# Prüfe verfügbare Geräte
python -c "import torch; print(torch.cuda.device_count())"
```

### Memory Errors

- Reduziere Batch-Size im Code
- Verwende CPU-Fallback: `device="cpu"`
- Schließe andere GPU-intensive Anwendungen

### Intel GPU Support

Intel Iris und andere integrierte GPUs haben begrenzte ML-Acceleration:

- PyTorch unterstützt Intel GPUs nicht nativ
- OpenVINO könnte als Alternative verwendet werden
- CPU-Performance ist oft vergleichbar mit integrierter GPU

## Monitoring

Der Service loggt beim Start:

```
Using device: cuda
CUDA available: 1 GPU(s) detected
Primary GPU: NVIDIA GeForce RTX 4080 (16.0 GB)
Embedding model loaded successfully on cuda
```

Verwende den `/device-info` Endpoint für Runtime-Informationen.
