#!/usr/bin/env python3
"""
llama.cpp metrics summary — reads metrics.log and prints a summary table.
Usage: python3 summary.py [N lines]
"""

import sys
import json
from datetime import datetime

def main():
    import urllib.request
    log_file = "/home/tyrel/projects/llama.cpp_monitoring/metrics.log"
    server_url = "http://localhost:9090"
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    # Fetch model info from server
    model_name, model_size_bytes = "N/A", 0
    try:
        with urllib.request.urlopen(f"{server_url}/models", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            if models:
                model_name = models[0].get("name", "N/A")
            data_list = data.get("data", [])
            if data_list:
                meta = data_list[0].get("meta", {})
                model_size_bytes = meta.get("size", 0)
    except Exception:
        pass
    
    def fmt_bytes(b):
        if b < 1024:
            return f"{b:.0f} B"
        elif b < 1024**2:
            return f"{b/1024:.1f} KB"
        elif b < 1024**3:
            return f"{b/1024**2:.1f} MB"
        else:
            return f"{b/1024**3:.2f} GB"
    
    records = []
    try:
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        print(f"No log file found at {log_file}")
        return
    
    if not records:
        print("No records found.")
        return
    
    # Filter valid records
    valid = [r for r in records if "tokens_per_second" in r]
    if not valid:
        print("No valid metrics records found.")
        return
    
    # Get last N records
    tail = valid[-n:]
    
    tps_values = [r["tokens_per_second"] for r in tail if r["tokens_per_second"] > 0]
    
    print("=" * 60)
    print(f"  llama.cpp Metrics Summary (last {len(tail)} samples)")
    print("=" * 60)
    print()
    
    if tps_values:
        print(f"  Tokens/sec:     min={min(tps_values):.1f}  max={max(tps_values):.1f}  avg={sum(tps_values)/len(tps_values):.1f}")
    else:
        print(f"  Tokens/sec:     no active generation")
    
    # Prompt t/s from log (cumulative avg)
    prompt_tps_values = []
    for r in tail:
        pt = r.get("total_prompt_tokens", 0)
        # Compute prompt t/s from cumulative values in log
        if pt > 0:
            prompt_tps_values.append(pt)
    
    print(f"  Model:          {model_name}")
    print(f"  Size:           {fmt_bytes(model_size_bytes)}")
    
    print()
    print(f"  Log file:       {log_file}")
    print(f"  Records:        {len(valid)} total, {len(tail)} shown")
    print(f"  Time range:     {tail[0]['timestamp']} → {tail[-1]['timestamp']}")
    print()
    
    # Recent samples
    print(f"  {'Time':<22s} {'t/s':>8s} {'Prompt t/s':>10s} {'Requests':>10s} {'Queued':>8s}")
    print(f"  {'-'*22} {'-'*8} {'-'*10} {'-'*10} {'-'*8}")
    for r in tail[-15:]:
        tps = f"{r['tokens_per_second']:.1f}" if r.get('tokens_per_second', 0) > 0 else "—"
        pt = f"{r['prompt_tokens_per_second']:.1f}" if r.get('prompt_tokens_per_second', 0) > 0 else "—"
        ts = r.get("timestamp", "")[-8:] if "timestamp" in r else "?"
        req = str(int(r.get("requests_processing", r.get("requests_total", 0))))
        queued = str(int(r.get("requests_deferred", 0)))
        print(f"  {ts:<22s} {tps:>8s} {pt:>10s} {req:>10s} {queued:>8s}")
    print()


if __name__ == "__main__":
    main()
