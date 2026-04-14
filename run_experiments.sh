#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GEM5_DIR="$ROOT_DIR/gem5"
GEM5_BIN=${GEM5_BIN:-"$GEM5_DIR/build/X86/gem5.opt"}
CONFIG_PY="$ROOT_DIR/configs/run_se.py"
BENCH_DIR="$ROOT_DIR/benchmarks"
BENCH_BIN_DIR="$BENCH_DIR/bin"
RESULTS_DIR=${RESULTS_DIR:-"$ROOT_DIR/results"}

MATRIX_SIZE=${MATRIX_SIZE:-96}
MATRIX_REPS=${MATRIX_REPS:-4}
POINTER_NODES=${POINTER_NODES:-262144}
POINTER_STEPS_PER_NODE=${POINTER_STEPS_PER_NODE:-2}
POINTER_SEED=${POINTER_SEED:-12345}
TOTAL_CASES=4

if [[ -z "${CONDA_PREFIX:-}" ]] || [[ "$(basename "$CONDA_PREFIX")" != "gem5-hpcs" ]]; then
    echo "Activate the conda environment first: conda activate gem5-hpcs" >&2
    exit 1
fi

if [[ ! -x "$GEM5_BIN" ]]; then
    echo "gem5 binary not found: $GEM5_BIN" >&2
    exit 1
fi

if [[ ! -x "$BENCH_BIN_DIR/matrix_multiply" || ! -x "$BENCH_BIN_DIR/pointer_chase" ]]; then
    "$BENCH_DIR/build.sh"
fi

mkdir -p "$RESULTS_DIR"

format_duration() {
    local total_seconds=$1
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    printf '%02d:%02d:%02d' "$hours" "$minutes" "$seconds"
}

run_case() {
    local case_index=$1
    local name=$2
    local cpu=$3
    local binary=$4
    local binary_args=$5
    local outdir="$RESULTS_DIR/$name"
    local logfile="$outdir/run.log"
    local case_start
    local case_end
    local case_elapsed
    local overall_now
    local overall_elapsed

    mkdir -p "$outdir"
    case_start=$(date +%s)
    overall_now=$(date +%s)
    overall_elapsed=$((overall_now - OVERALL_START))

    echo
    echo "[$case_index/$TOTAL_CASES] Starting $name"
    echo "  CPU: $cpu"
    echo "  Binary: $binary"
    echo "  Args: $binary_args"
    echo "  Output: $outdir"
    echo "  Overall elapsed: $(format_duration "$overall_elapsed")"

    "$GEM5_BIN" -d "$outdir" "$CONFIG_PY" \
        --cpu "$cpu" \
        --binary "$binary" \
        --binary-args "$binary_args" | tee "$logfile"

    case_end=$(date +%s)
    case_elapsed=$((case_end - case_start))

    echo "[$case_index/$TOTAL_CASES] Finished $name in $(format_duration "$case_elapsed")"
    echo "  stats: $outdir/stats.txt"
    echo "  log: $logfile"
}

OVERALL_START=$(date +%s)

run_case \
    1 \
    "matrix_minor" \
    "minor" \
    "$BENCH_BIN_DIR/matrix_multiply" \
    "$MATRIX_SIZE $MATRIX_REPS"

run_case \
    2 \
    "matrix_o3" \
    "o3" \
    "$BENCH_BIN_DIR/matrix_multiply" \
    "$MATRIX_SIZE $MATRIX_REPS"

run_case \
    3 \
    "pointer_minor" \
    "minor" \
    "$BENCH_BIN_DIR/pointer_chase" \
    "$POINTER_NODES $POINTER_STEPS_PER_NODE $POINTER_SEED"

run_case \
    4 \
    "pointer_o3" \
    "o3" \
    "$BENCH_BIN_DIR/pointer_chase" \
    "$POINTER_NODES $POINTER_STEPS_PER_NODE $POINTER_SEED"

OVERALL_END=$(date +%s)
echo
echo "Finished all experiments in $(format_duration "$((OVERALL_END - OVERALL_START))")."
echo "Results are in $RESULTS_DIR"
