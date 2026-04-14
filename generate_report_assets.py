#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


WORKLOAD_ORDER = ["matrix", "pointer"]
CPU_ORDER = ["minor", "o3"]
METRICS = [
    ("ipc", "IPC", "ipc.png"),
    ("cpi", "CPI", "cpi.png"),
    ("num_cycles", "Cycles", "num_cycles.png"),
    ("l1d_miss_rate", "L1D Miss Rate", "l1d_miss_rate.png"),
    ("l2_miss_rate", "L2 Miss Rate", "l2_miss_rate.png"),
]


def load_rows(summary_path: Path):
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        for key in (
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
        ):
            row[key] = float(row[key])

    return sorted(
        rows,
        key=lambda row: (
            WORKLOAD_ORDER.index(row["workload"]),
            CPU_ORDER.index(row["cpu"]),
        ),
    )


def format_int(value: float) -> str:
    return f"{int(round(value)):,}"


def format_ratio(value: float) -> str:
    return f"{value:.6f}"


def write_markdown_table(rows, output_path: Path):
    lines = [
        "# Report Table",
        "",
        "| Workload | CPU | Sim Insts | Cycles | IPC | CPI | L1D Miss Rate | L2 Miss Rate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        lines.append(
            "| {workload} | {cpu} | {sim_insts} | {num_cycles} | {ipc} | {cpi} | {l1d_miss_rate} | {l2_miss_rate} |".format(
                workload=row["workload"],
                cpu=row["cpu"],
                sim_insts=format_int(row["sim_insts"]),
                num_cycles=format_int(row["num_cycles"]),
                ipc=format_ratio(row["ipc"]),
                cpi=format_ratio(row["cpi"]),
                l1d_miss_rate=format_ratio(row["l1d_miss_rate"]),
                l2_miss_rate=format_ratio(row["l2_miss_rate"]),
            )
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_metric_plot(rows, metric_key: str, metric_label: str, output_path: Path):
    workloads = WORKLOAD_ORDER
    minor_values = []
    o3_values = []

    for workload in workloads:
        workload_rows = {row["cpu"]: row for row in rows if row["workload"] == workload}
        minor_values.append(workload_rows["minor"][metric_key])
        o3_values.append(workload_rows["o3"][metric_key])

    x_positions = list(range(len(workloads)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        [x - width / 2 for x in x_positions],
        minor_values,
        width=width,
        label="MinorCPU",
        color="#4C78A8",
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        o3_values,
        width=width,
        label="O3CPU",
        color="#F58518",
    )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([workload.title() for workload in workloads])
    ax.set_ylabel(metric_label)
    ax.set_title(f"{metric_label} by Workload and CPU")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Generate report-ready tables and plots from summary.csv."
    )
    parser.add_argument(
        "--summary",
        default="/home/asen/Work/Uni Work/Година 3/Семестър 6/ВПКС/CourseWork/results/summary.csv",
        help="Path to summary.csv produced by extract_stats.py.",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/asen/Work/Uni Work/Година 3/Семестър 6/ВПКС/CourseWork/results/report_assets",
        help="Directory where the markdown table and plots will be written.",
    )
    args = parser.parse_args()

    summary_path = Path(args.summary).resolve()
    if not summary_path.is_file():
        raise FileNotFoundError(f"summary.csv not found: {summary_path}")

    output_dir = Path(args.output_dir).resolve()
    plots_dir = output_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(summary_path)
    write_markdown_table(rows, output_dir / "report_table.md")

    for metric_key, metric_label, filename in METRICS:
        build_metric_plot(rows, metric_key, metric_label, plots_dir / filename)

    print(f"Wrote report assets to {output_dir}")


if __name__ == "__main__":
    main()
