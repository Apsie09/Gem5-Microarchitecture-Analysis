#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC_DIR="$ROOT_DIR/src"
BIN_DIR="$ROOT_DIR/bin"

CC=${CC:-gcc}
CFLAGS=${CFLAGS:--O2 -std=c11 -Wall -Wextra -Wpedantic -march=x86-64 -mtune=generic -fno-tree-vectorize}

mkdir -p "$BIN_DIR"

"$CC" $CFLAGS "$SRC_DIR/matrix_multiply.c" -o "$BIN_DIR/matrix_multiply"
"$CC" $CFLAGS "$SRC_DIR/pointer_chase.c" -o "$BIN_DIR/pointer_chase"

echo "Built:"
echo "  $BIN_DIR/matrix_multiply"
echo "  $BIN_DIR/pointer_chase"
