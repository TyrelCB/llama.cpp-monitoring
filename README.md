# llama.cpp Server Monitor

Real-time monitoring for llama.cpp server via Prometheus metrics endpoint.

## Setup

```bash
cd ~/projects/llama.cpp_monitoring
```

## Usage

### 1. Real-time terminal monitor
```bash
python3 monitor.py
```
Polls `/metrics` every 2 seconds and displays tokens/sec, VRAM usage, and request count.

### 2. Background logging
```bash
python3 log_metrics.py
```
Polls every 5 seconds, writes JSON lines to `metrics.log`. Runs until Ctrl+C.

### 3. Summary view
```bash
python3 summary.py          # Last 50 samples
python3 summary.py 200      # Last 200 samples
```

### 4. Graph/plot
```bash
python3 graph.py            # Plot last 200 samples → plot.png
python3 graph.py 500        # Plot last 500 samples → plot.png
```

## Files

| File | Purpose |
|---|---|
| `monitor.py` | Real-time terminal monitor |
| `log_metrics.py` | Background JSON logger |
| `summary.py` | Text summary of logged data |
| `graph.py` | Generates `plot.png` chart |

## Prerequisites

- llama.cpp server running with `--metrics` flag
- Python 3 with `matplotlib` (for graph.py)

```bash
# Install matplotlib if needed
pip install matplotlib
```
