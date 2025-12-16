#!/usr/bin/env bash
# 容器 smoke 测试：构建镜像并运行一次源码模式扫描，验证退出码与报告生成。

set -euo pipefail

IMG="${IMG:-minos:test}"
WORKDIR="${WORKDIR:-/work}"
OUTDIR="${OUTDIR:-output/reports}"

echo "[smoke] build image ${IMG}"
docker build -t "${IMG}" .

echo "[smoke] run source-mode scan"
docker run --rm \
  -v "$PWD":${WORKDIR} -w ${WORKDIR} \
  "${IMG}" \
  minos scan --mode source --input tests --output-dir "${OUTDIR}" --format json --log-level info

echo "[smoke] run apk-mode error case"
if docker run --rm \
  -v "$PWD":${WORKDIR} -w ${WORKDIR} \
  "${IMG}" \
  minos scan --mode apk --apk-path tests/fixtures/missing.apk --format json; then
  echo "[smoke] apk-mode missing input should fail but succeeded" >&2
  exit 1
else
  echo "[smoke] apk-mode missing input failed as expected"
fi

echo "[smoke] done. Reports should be under ${OUTDIR}."
