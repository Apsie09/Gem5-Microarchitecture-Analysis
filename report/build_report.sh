#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUILD_DIR="$ROOT_DIR/build"

mkdir -p "$BUILD_DIR"

cd "$ROOT_DIR"

pdflatex -interaction=nonstopmode -output-directory="$BUILD_DIR" main.tex
pdflatex -interaction=nonstopmode -output-directory="$BUILD_DIR" main.tex

cp -f "$BUILD_DIR/main.pdf" "$ROOT_DIR/main.pdf"

echo "Built report:"
echo "  $BUILD_DIR/main.pdf"
