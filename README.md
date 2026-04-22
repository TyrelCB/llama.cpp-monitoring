# llama.cpp Monitoring

Real-time monitoring and visualization for llama.cpp servers.

## Quick Start

### 1. Start the llama.cpp server
```bash
llamacpp
```

### 2. Start the monitoring stack
```bash
docker compose up -d
```

### 3. Access the services
- **Grafana**: http://localhost:3000 (admin/grafana)
- **Prometheus**: http://localhost:9191

## Dashboard

The "llama.cpp Monitor" dashboard includes:

### Throughput
- **Tokens/sec** — Generation and prompt throughput
- **Requests Processing** — Currently active requests
- **Requests Queued** — Deferred requests waiting for capacity

### Cumulative
- **Total Tokens** — Generated vs prompt tokens over time
- **Processing Time** — Cumulative generation and prompt time

### Latency
- **Prompt Latency** — Time to process prompt tokens
- **Sampling Latency** — Time per token generation

## CLI Tools

Still available alongside Grafana:
```bash
python3 monitor.py      # Real-time terminal monitor
python3 log_metrics.py & # Background logger
python3 summary.py      # Stats from metrics.log
python3 graph.py        # Generate plot.png
```

## Stopping
```bash
docker compose down
```
