#!/usr/bin/env bash
# CI 示例脚本：构建镜像并运行一次源码模式扫描，生成报告到 artifacts 目录。

set -euo pipefail

IMG="${IMG:-minos:ci}"
WORKDIR="${WORKDIR:-/work}"
OUTDIR="${OUTDIR:-/work/output/reports}"
SRC="${SRC:-tests}"

echo "[ci] build image ${IMG}"
docker build -t "${IMG}" .

echo "[ci] run source-mode scan -> ${OUTDIR}"
docker run --rm \
  -v "$PWD":${WORKDIR} -w ${WORKDIR} \
  "${IMG}" \
  minos scan --mode source --input "${SRC}" --output-dir "${OUTDIR}" --format json

echo "[ci] reports written to ${OUTDIR} (host: $(pwd)/output/reports)"
