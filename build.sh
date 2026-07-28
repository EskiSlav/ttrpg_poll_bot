#!/usr/bin/env bash
set -euo pipefail

# Produces the Lambda deployment package — the Python equivalent of the website
# backend's esbuild step. Used both by Terraform's source_path (initial apply/import
# only) and by CI's deploy workflow (every code push, via `aws lambda update-function-code`).

rm -rf build
mkdir -p build

# --platform/--python-version/--only-binary force pip to fetch Lambda-compatible (Amazon
# Linux, x86_64) wheels regardless of the host machine running this script — without
# this, a dependency with a compiled extension (e.g. requests -> charset_normalizer,
# which ships a native mypyc .so) gets built for the LOCAL machine's OS instead, and
# fails to import at all once uploaded to Lambda.
pip install \
  --platform manylinux2014_x86_64 \
  --python-version 3.14 \
  --implementation cp \
  --only-binary=:all: \
  --target build \
  --quiet \
  -r requirements.txt
cp lambda_handler.py build/

echo "Built build/ ($(du -sh build | cut -f1))"
