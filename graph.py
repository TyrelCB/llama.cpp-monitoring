#!/usr/bin/env python3
"""
llama.cpp real-time graph — plots t/s and VRAM over time using matplotlib.
Usage: python3 graph.py [N lines]
"""

import sys
import json
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

def main():
    log_file = "/home/tyrel/projects/llama.cpp_monitoring/metrics.log"
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    
    records = []
    with open(log_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    valid = [r for r in records if "tokens_per_second" in r and "error" not in r]
    if not valid:
        print("No valid records found.")
        return
    
    tail = valid[-n:]
    
    tps = [r.get("tokens_per_second", 0) for r in tail]
    requests = [r.get("requests_processing", r.get("requests_total", 0)) for r in tail]
    x = list(range(len(tail)))
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))
    
    ax.plot(x, tps, color="tab:blue", linewidth=1.2)
    ax.set_ylabel("Tokens/sec", fontsize=12)
    ax.set_title("llama.cpp Performance Monitor", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    if tps:
        ax.axhline(y=sum(tps)/len(tps), color="gray", linestyle="--", alpha=0.5, label=f"Avg: {sum(tps)/len(tps):.1f}")
        ax.legend(loc="upper right")
    ax.set_xlabel("Sample", fontsize=12)
    
    plt.tight_layout()
    plt.savefig("/home/tyrel/projects/llama.cpp_monitoring/plot.png", dpi=100)
    print(f"Plot saved to plot.png ({len(tail)} samples)")


if __name__ == "__main__":
    main()
