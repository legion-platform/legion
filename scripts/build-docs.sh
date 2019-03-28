#!/usr/bin/env bash
set -e

cd docs

sphinx-apidoc -f --private -o source/ ../legion/ -V "${BUILD_VERSION}"
sed -i "s/1.0/${BUILD_VERSION}/" source/conf.py
make html
find build/html -type f -name '*.html' | xargs sed -i -r 's/href=\"(.*)\\.md\"/href=\"\\1.html\"/'

cd ..
tar -czf legion_docs_${BUILD_VERSION}.tar.gz docs/build/html/