#!/usr/bin/env sh

SRC_DIR=source
OUT_DIR=out

echo "Building of HTML docs"
sphinx-build -b html $SRC_DIR $OUT_DIR

echo "Building of PDF docs"
sphinx-build -b pdf $SRC_DIR $OUT_DIR/pdf
