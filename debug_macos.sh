#!/bin/bash
# macOS 调试启动脚本 - 捕获所有 stderr 排查闪退
# 用法：bash debug_macos.sh
set -e

APP_PATH="dist/迅鲨加速器.app"
if [ ! -d "$APP_PATH" ]; then
  APP_PATH="dist2/迅鲨加速器.app"
fi
if [ ! -d "$APP_PATH" ]; then
  APP_PATH="dist3/迅鲨加速器.app"
fi
if [ ! -d "$APP_PATH" ]; then
  echo "ERR 找不到 .app，请确认 dist/ 下有 迅鲨加速器.app"
  exit 1
fi

EXEC="$APP_PATH/Contents/MacOS/迅鲨加速器"

if [ ! -f "$EXEC" ]; then
  echo "ERR 找不到可执行文件: $EXEC"
  echo "   目录内容:"
  ls -la "$APP_PATH/Contents/MacOS/"
  exit 1
fi

# 1) 先去 quarantine
xattr -cr "$APP_PATH" 2>/dev/null || true

echo "=========================================="
echo " 启动: $EXEC"
echo " 工作目录: $(pwd)"
echo "=========================================="
echo "如果闪退，会在这里看到错误信息"
echo "按 Ctrl+C 退出"
echo ""

# 2) 直接执行并捕获所有输出
"$EXEC" 2>&1 | tee /tmp/easytier-client.log
