#!/bin/bash
# Smart Ops CLI 打包脚本
# 用于在有 Python + PyInstaller 的机器上生成独立二进制
# 生成文件: dist/smart-ops (x86_64) 或 dist/smart-ops-arm64 (ARM)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH="$(uname -m)"
cd "$SCRIPT_DIR"

echo "=== Smart Ops CLI 打包 ==="
echo "架构: $ARCH  |  Python: $(python3 --version)"

# 确保 PyInstaller 可用
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "安装 PyInstaller..."
    pip3 install pyinstaller --break-system-packages -q 2>/dev/null || \
    pip3 install pyinstaller -q
fi

# 确定输出文件名
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    OUTPUT_NAME="smart-ops-arm64"
else
    OUTPUT_NAME="smart-ops"
fi

echo "开始打包 -> dist/$OUTPUT_NAME ..."

pyinstaller \
    --onefile \
    --name "$OUTPUT_NAME" \
    --hidden-import psutil \
    --hidden-import yaml \
    --hidden-import jinja2 \
    --hidden-import click \
    --hidden-import src.core.system \
    --hidden-import src.core.health \
    --hidden-import src.core.port_scanner \
    --hidden-import src.core.process_monitor \
    --hidden-import src.core.report_generator \
    --hidden-import src.core.history \
    --hidden-import src.utils \
    --collect-data jinja2 \
    --clean \
    --noconfirm \
    tool

echo ""
echo "✅ 打包完成: dist/$OUTPUT_NAME"
ls -lh "dist/$OUTPUT_NAME"

# 同时打包离线wheel（给有Python无网络的机器用）
echo ""
echo "下载离线依赖wheel..."
mkdir -p dist/wheels
pip3 download psutil click pyyaml jinja2 \
    -d dist/wheels -q 2>/dev/null && \
    echo "✅ 离线wheel已保存到 dist/wheels/" || \
    echo "⚠️  wheel下载失败（无网络），跳过"

echo ""
echo "=== 产物清单 ==="
echo "  dist/$OUTPUT_NAME     - 独立二进制（无需Python）"
echo "  dist/wheels/          - 离线pip依赖（有Python无网络时用）"
echo ""
echo "部署到目标机器："
echo "  scp dist/$OUTPUT_NAME user@host:/usr/local/bin/tool"
echo "  # 或"
echo "  scp -r dist/ deploy.sh user@host:/opt/smart-ops/ && ssh user@host 'cd /opt/smart-ops && bash deploy.sh'"
