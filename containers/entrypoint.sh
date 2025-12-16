#!/bin/sh
# Minos 容器入口：默认执行 CLI，支持通过挂载工作目录与规则缓存运行扫描。

set -e

if [ "$1" = "" ]; then
  set -- minos "$@"
fi

if [ "$1" = "minos" ]; then
  shift
  exec python -m minos.cli "$@"
fi

# 允许传入自定义命令，例如 /bin/sh
exec "$@"
