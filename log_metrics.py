#!/usr/bin/env python3
"""
llama.cpp metrics JSON logger
Polls /metrics and writes structured JSON to a log file for analysis.
"""

import sys
import time
import json
import urllib.request
import signal
from datetime import datetime

SERVER_URL = "http://localhost:9090"
POLL_INTERVAL = 5
LOG_FILE = "/home/tyrel/projects/llama.cpp_monitoring/metrics.log"

running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def parse_metrics(text):
    metrics = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "{" in line:
            parts = line.split("{", 1)
            name = parts[0].strip()
            rest = parts[1]
            val_part = rest.split("}", 1)[1].strip()
            value = float(val_part.split()[0])
            label_str = rest.split("}", 1)[0]
            labels = {}
            for pair in label_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    labels[k] = v.strip('"')
            metrics[name] = {"value": value, "labels": labels}
        else:
            parts = line.split()
            raw_name = parts[0].strip()
            # Support both "llamacpp:metric" and "llamacpp_metric" formats
            name = raw_name.replace("llamacpp:", "llamacpp_")
            value = float(parts[1]) if len(parts) > 1 else 0
            metrics[name] = {"value": value, "labels": {}}
    return metrics


def main():
    global running
    print(f"Logging metrics to {LOG_FILE} (Ctrl+C to stop)")
    
    with open(LOG_FILE, "w") as f:
        while running:
            try:
                url = f"{SERVER_URL}/metrics"
                with urllib.request.urlopen(url, timeout=3) as resp:
                    raw = resp.read().decode("utf-8")
                    metrics = parse_metrics(raw)
                    
                    # Flatten for easy parsing
                    total_tokens = metrics.get("llamacpp_tokens_predicted_total", {}).get("value", 0)
                    total_time = metrics.get("llamacpp_tokens_predicted_seconds_total", {}).get("value", 0)
                    tps = total_tokens / total_time if total_time > 0 else 0
                    
                    # Prompt t/s
                    prompt_total = metrics.get("llamacpp_prompt_tokens_total", {}).get("value", 0)
                    prompt_time = metrics.get("llamacpp_prompt_seconds_total", {}).get("value", 0)
                    prompt_tps = prompt_total / prompt_time if prompt_time > 0 else 0
                    
                    record = {
                        "timestamp": datetime.now().isoformat(),
                        "tokens_per_second": tps,
                        "prompt_tokens_per_second": prompt_tps,
                        "total_tokens_predicted": total_tokens,
                        "total_prompt_tokens": prompt_total,
                        "cuda_memory_used_bytes": metrics.get("llamacpp_cuda_memory_used_bytes", {}).get("value", 0),
                        "cuda_memory_total_bytes": metrics.get("llamacpp_cuda_memory_total_bytes", {}).get("value", 0),
                        "cuda_memory_reserved_bytes": metrics.get("llamacpp_cuda_memory_reserved_bytes", {}).get("value", 0),
                        "requests_processing": metrics.get("llamacpp_requests_processing", {}).get("value", 0),
                        "requests_deferred": metrics.get("llamacpp_requests_deferred", {}).get("value", 0),
                    }
                    
                    line = json.dumps(record)
                    f.write(line + "\n")
                    f.flush()
            except Exception as e:
                error_record = {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                f.write(json.dumps(error_record) + "\n")
                f.flush()
            
            sleep_start = time.time()
            while running and (time.time() - sleep_start) < POLL_INTERVAL:
                time.sleep(0.05)


if __name__ == "__main__":
    main()
