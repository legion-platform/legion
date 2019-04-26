#!/usr/bin/env sh

SRC_DIR=source
OUT_DIR=out

sphinx-build -b html $SRC_DIR $OUT_DIR
sphinx-build -b rinoh $SRC_DIR $OUT_DIR-pdf
#find $OUT_DIR -type f -name '*.html' | xargs sed  -i'' '/href="\./s/\.md/\.html/'