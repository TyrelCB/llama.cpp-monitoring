#!/usr/bin/env python3
"""
llama.cpp server metrics monitor
Polls /metrics endpoint and displays real-time stats in terminal.
"""

import sys
import time
import json
import urllib.request
import signal
from datetime import datetime

# Config
SERVER_URL = "http://localhost:9090"
POLL_INTERVAL = 2  # seconds
REFRESH_RATE = 10  # characters per second for smooth updates

# State
running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def fetch_model_name(url):
    """Fetch model info from /models endpoint."""
    try:
        with urllib.request.urlopen(f"{url}/models", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            if models:
                name = models[0].get("name", "N/A")
            else:
                name = None
            # Size is in data[0].meta.size
            size_bytes = 0
            data_list = data.get("data", [])
            if data_list:
                meta = data_list[0].get("meta", {})
                size_bytes = meta.get("size", 0)
            return name, size_bytes
    except Exception:
        pass
    return None, 0


def parse_metrics(text):
    """Parse Prometheus metrics format into a dict."""
    metrics = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Parse: metric_name{labels} value  or  metric_name value
        if "{" in line:
            parts = line.split("{", 1)
            name = parts[0].strip()
            rest = parts[1]
            val_part = rest.split("}", 1)[1].strip()
            parts2 = val_part.split()
            value = float(parts2[0])
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


def format_bytes(b):
    if b < 1024:
        return f"{b:.0f} B"
    elif b < 1024**2:
        return f"{b/1024:.1f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.1f} MB"
    else:
        return f"{b/1024**3:.2f} GB"


def format_tps(tps):
    if tps > 0:
        return f"{tps:.1f} t/s"
    return "— t/s"


def display_header():
    """Clear screen and draw header."""
    # ANSI escape codes for terminal control
    sys.stdout.write("\033[2J\033[H")  # Clear screen, move to top
    w = 70
    print("╔" + "═" * w + "╗", end="")
    print()
    print("║" + " llama.cpp Server Monitor ".center(w) + "║")
    print("║" + f" Server: {SERVER_URL}  |  Poll: {POLL_INTERVAL}s".center(w) + "║")
    print("║" + f" Press Ctrl+C to stop".center(w) + "║")
    print("╚" + "═" * w + "╝", end="")
    print()


def display_metrics(metrics):
    """Display parsed metrics in a formatted table."""
    inner_w = 68  # inner content width (between │ │)
    
    # Extract key values
    total_tokens = metrics.get("llamacpp_tokens_predicted_total", {}).get("value", 0)
    total_time = metrics.get("llamacpp_tokens_predicted_seconds_total", {}).get("value", 0)
    tps = total_tokens / total_time if total_time > 0 else 0
    req_processing = metrics.get("llamacpp_requests_processing", {}).get("value", 0)
    req_deferred = metrics.get("llamacpp_requests_deferred", {}).get("value", 0)
    prompt_tps = metrics.get("llamacpp_prompt_tokens_seconds", {}).get("value", 0)
    
    model_name, model_size_bytes = fetch_model_name(SERVER_URL)
    if model_name is None:
        model_info = metrics.get("llamacpp_loaded_model_info", {})
        model_name = model_info.get("labels", {}).get("name", "N/A")
        model_size_bytes = model_info.get("labels", {}).get("size_bytes", 0)
    
    model_size = format_bytes(model_size_bytes)
    
    # Display requests processing count (newer llama.cpp doesn't have requests_total)
    req_display = f"Processing: {int(req_processing)}"
    
    # Model line — cap to fit in box
    model_display = f"│  Model: {model_name}"
    if len(model_display) > inner_w + 4:
        model_display = f"│  Model: {model_name[:inner_w - 11]}"
    model_display = model_display.ljust(inner_w + 4) + "│"
    size_display = f"│  Size: {model_size}".ljust(inner_w + 4) + "│"
    
    print()
    print(f"┌{'─' * (inner_w + 2)}┐")
    print(f"│  Performance".ljust(inner_w + 4) + "│")
    print(f"├{'─' * (inner_w + 2)}┤")
    print(f"│  Tokens/sec: {format_tps(tps)}".ljust(inner_w + 4) + "│")
    print(f"│  Prompt t/s: {format_tps(prompt_tps)}".ljust(inner_w + 4) + "│")
    print(f"│  {req_display}  Queued: {int(req_deferred)}")
    print(f"├{'─' * (inner_w + 2)}┤")
    print(model_display)
    print(size_display)
    print(f"└{'─' * (inner_w + 2)}┘")
    
    # Additional metrics
    perf_metrics = {k: v for k, v in metrics.items() if "perf" in k.lower()}
    if perf_metrics:
        print()
        print(f"┌{'─' * (inner_w + 2)}┐")
        print(f"│  Detailed Performance".ljust(inner_w + 4) + "│")
        print(f"├{'─' * (inner_w + 2)}┤")
        for name, data in list(perf_metrics.items())[:5]:
            label = name.split("_")[-1].replace("_", " ").title()
            print(f"│  {label}: {data['value']:.2f}".ljust(inner_w + 4) + "│")
        print(f"└{'─' * (inner_w + 2)}┘")
    
    print()
    print(f"  Updated: {datetime.now().strftime('%H:%M:%S')}  |  {POLL_INTERVAL}s poll interval", end="")
    print("\033[K")  # Clear to end of line


def main():
    global running
    
    sys.stdout.write("\033[?25l")  # Hide cursor
    display_header()
    
    while running:
        try:
            url = f"{SERVER_URL}/metrics"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                raw = resp.read().decode("utf-8")
                metrics = parse_metrics(raw)
        except Exception as e:
            metrics = {}
        
        # Re-draw header every 30 seconds, then just update metrics
        display_metrics(metrics)
        
        sys.stdout.flush()
        
        # Smooth sleep
        sleep_start = time.time()
        while running and (time.time() - sleep_start) < POLL_INTERVAL:
            time.sleep(0.05)
    
    sys.stdout.write("\033[?25h")  # Show cursor
    print()
    print("Monitor stopped.")


if __name__ == "__main__":
    main()
