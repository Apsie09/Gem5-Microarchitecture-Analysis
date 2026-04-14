#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
from typing import Dict, List


STAT_CANDIDATES = {
    "sim_ticks": ["simTicks"],
    "sim_insts": ["simInsts"],
    "host_seconds": ["hostSeconds"],
    "num_cycles": ["board.processor.cores.core.numCycles"],
    "ipc": [
        "board.processor.cores.core.ipc",
        "board.processor.cores.core.commitStats0.ipc",
    ],
    "cpi": [
        "board.processor.cores.core.cpi",
        "board.processor.cores.core.commitStats0.cpi",
    ],
    "l1d_miss_rate": [
        "board.cache_hierarchy.l1d-cache-0.overallMissRate::total",
        "board.cache_hierarchy.l1d-cache-0.demandMissRate::total",
    ],
    "l1d_avg_miss_latency_ticks": [
        "board.cache_hierarchy.l1d-cache-0.overallAvgMissLatency::total",
        "board.cache_hierarchy.l1d-cache-0.demandAvgMissLatency::total",
    ],
    "l2_miss_rate": [
        "board.cache_hierarchy.l2-cache-0.overallMissRate::total",
        "board.cache_hierarchy.l2-cache-0.ReadSharedReq.missRate::total",
    ],
    "l2_avg_miss_latency_ticks": [
        "board.cache_hierarchy.l2-cache-0.overallAvgMissLatency::total",
        "board.cache_hierarchy.l2-cache-0.ReadSharedReq.avgMissLatency::total",
    ],
}


def parse_stats(stats_path: Path) -> Dict[str, str]:
    stats: Dict[str, str] = {}

    with stats_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("-"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            name = parts[0]
            value = parts[1]
            stats[name] = value

    return stats


def pick_stat(stats: Dict[str, str], candidates: List[str]) -> str:
    for candidate in candidates:
        if candidate in stats:
            return stats[candidate]
    return ""


def infer_case_metadata(case_name: str) -> Dict[str, str]:
    lower = case_name.lower()
    workload = ""
    cpu = ""

    if "matrix" in lower:
        workload = "matrix"
    elif "pointer" in lower:
        workload = "pointer"

    if "minor" in lower:
        cpu = "minor"
    elif "o3" in lower:
        cpu = "o3"

    return {"workload": workload, "cpu": cpu}


def collect_rows(results_dir: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    for case_dir in sorted(path for path in results_dir.iterdir() if path.is_dir()):
        stats_path = case_dir / "stats.txt"
        if not stats_path.is_file() or stats_path.stat().st_size == 0:
            continue

        stats = parse_stats(stats_path)
        metadata = infer_case_metadata(case_dir.name)
        row: Dict[str, str] = {
            "case": case_dir.name,
            "workload": metadata["workload"],
            "cpu": metadata["cpu"],
        }

        for column, candidates in STAT_CANDIDATES.items():
            row[column] = pick_stat(stats, candidates)

        rows.append(row)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract key gem5 metrics from coursework results into a CSV file."
    )
    parser.add_argument(
        "--results-dir",
        default="/home/asen/Work/Uni Work/Година 3/Семестър 6/ВПКС/CourseWork/results",
        help="Directory containing per-run gem5 output folders.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional CSV output path. Defaults to <results-dir>/summary.csv.",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    if not results_dir.is_dir():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    output_path = (
        Path(args.output).resolve()
        if args.output
        else results_dir / "summary.csv"
    )

    rows = collect_rows(results_dir)
    if not rows:
        raise RuntimeError(
            f"No non-empty stats.txt files found under {results_dir}"
        )

    fieldnames = [
        "case",
        "workload",
        "cpu",
        "sim_ticks",
        "sim_insts",
        "host_seconds",
        "num_cycles",
        "ipc",
        "cpi",
        "l1d_miss_rate",
        "l1d_avg_miss_latency_ticks",
        "l2_miss_rate",
        "l2_avg_miss_latency_ticks",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ in ("__main__", "__m5_main__"):
    main()
