"""Hammer /tickets with concurrent requests and report latency + error rate.

    python scripts/loadtest.py --n 300 --c 16 [--url http://localhost:8080]
Run against rules mode to measure the service itself (no model latency in the way).
"""
import argparse
import json
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

SAMPLES = json.loads((Path(__file__).resolve().parent.parent / "data" / "sample_tickets.json").read_text())


def one(client: httpx.Client, url: str, i: int):
    t = SAMPLES[i % len(SAMPLES)]["text"] + f" (load {i})"
    t0 = time.perf_counter()
    try:
        r = client.post(f"{url}/tickets", json={"text": t, "source": "loadtest"}, timeout=30)
        return (time.perf_counter() - t0) * 1000, r.status_code, (r.text[:200] if r.status_code != 200 else "")
    except Exception as e:  # noqa: BLE001
        return (time.perf_counter() - t0) * 1000, 0, repr(e)[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--c", type=int, default=16)
    ap.add_argument("--url", default="http://localhost:8080")
    a = ap.parse_args()
    mode = httpx.get(f"{a.url}/health").json()["mode"]
    before = httpx.get(f"{a.url}/queues").json()["total"]
    t0 = time.perf_counter()
    with httpx.Client() as client, ThreadPoolExecutor(max_workers=a.c) as ex:
        results = list(ex.map(lambda i: one(client, a.url, i), range(a.n)))
    wall = time.perf_counter() - t0
    lat = sorted(r[0] for r in results)
    errs = [r for r in results if r[1] != 200]
    after = httpx.get(f"{a.url}/queues").json()["total"]
    print(f"mode={mode} n={a.n} concurrency={a.c} wall={wall:.2f}s rps={a.n / wall:.0f}")
    print(f"latency ms: p50={lat[len(lat) // 2]:.1f} p95={lat[int(len(lat) * .95) - 1]:.1f} p99={lat[int(len(lat) * .99) - 1]:.1f} max={lat[-1]:.1f} mean={statistics.mean(lat):.1f}")
    print(f"errors: {len(errs)}/{a.n}")
    for e in errs[:5]:
        print("  ", e[1], e[2])
    print(f"audit rows: before={before} after={after} (expected +{a.n - len(errs)}, got +{after - before})")
    return 1 if errs or after - before != a.n - len(errs) else 0


if __name__ == "__main__":
    sys.exit(main())
