#!/bin/bash
# Smart Ops CLI 部署脚本
# 自动检测环境，选择二进制或Python方式运行
# 支持: x86_64 (主) / aarch64 ARM (次)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH="$(uname -m)"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
BINARY_NAME="smart-ops"

echo "=== Smart Ops CLI 部署 ==="
echo "架构: $ARCH"

# ─── 方式1: 使用预编译二进制 ─────────────────────────────────
deploy_binary() {
    local binary="$SCRIPT_DIR/dist/smart-ops"

    # 按架构选择二进制
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        binary="$SCRIPT_DIR/dist/smart-ops-arm64"
    fi

    if [ -f "$binary" ]; then
        echo "使用预编译二进制: $binary"
        chmod +x "$binary"
        cp "$binary" "$INSTALL_DIR/tool"
        echo "✅ 已安装到 $INSTALL_DIR/tool"
        return 0
    fi
    return 1
}

# ─── 方式2: Python 环境 ──────────────────────────────────────
deploy_python() {
    local python_bin=""

    # 检测可用的Python命令
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local ver=$($cmd -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)" 2>/dev/null)
            if [ "${ver:-0}" -ge 39 ]; then
                python_bin="$cmd"
                echo "检测到 Python: $(command -v $cmd) ($($cmd --version 2>&1))"
                break
            fi
        fi
    done

    if [ -z "$python_bin" ]; then
        return 1
    fi

    # 安装依赖
    echo "安装依赖..."
    if $python_bin -m pip install -r "$SCRIPT_DIR/requirements.txt" -q 2>/dev/null; then
        echo "依赖安装完成"
    elif $python_bin -m pip install -r "$SCRIPT_DIR/requirements.txt" -q --break-system-packages 2>/dev/null; then
        echo "依赖安装完成 (break-system-packages)"
    else
        echo "⚠️  pip 安装失败，尝试检查依赖是否已存在..."
        $python_bin -c "import psutil, click, yaml, jinja2" 2>/dev/null || {
            echo "❌ 依赖缺失且无法安装"
            return 1
        }
    fi

    # 创建 wrapper 脚本
    cat > "$INSTALL_DIR/tool" << EOF
#!/bin/bash
exec $python_bin "$SCRIPT_DIR/tool" "\$@"
EOF
    chmod +x "$INSTALL_DIR/tool"
    echo "✅ 已创建 wrapper: $INSTALL_DIR/tool -> $python_bin"
    return 0
}

# ─── 方式3: 离线依赖包 ───────────────────────────────────────
deploy_offline() {
    local python_bin=""
    for cmd in python3 python; do
        command -v "$cmd" >/dev/null 2>&1 && { python_bin="$cmd"; break; }
    done
    [ -z "$python_bin" ] && return 1

    local wheels_dir="$SCRIPT_DIR/dist/wheels"
    [ -d "$wheels_dir" ] || return 1

    echo "使用离线wheel包安装依赖..."
    $python_bin -m pip install --no-index --find-links="$wheels_dir" \
        psutil click pyyaml jinja2 -q 2>/dev/null || \
    $python_bin -m pip install --no-index --find-links="$wheels_dir" \
        psutil click pyyaml jinja2 -q --break-system-packages 2>/dev/null || return 1

    cat > "$INSTALL_DIR/tool" << EOF
#!/bin/bash
exec $python_bin "$SCRIPT_DIR/tool" "\$@"
EOF
    chmod +x "$INSTALL_DIR/tool"
    echo "✅ 离线安装完成"
    return 0
}

# ─── 主流程 ─────────────────────────────────────────────────
main() {
    # 确保安装目录存在
    mkdir -p "$INSTALL_DIR"

    # 按优先级尝试
    if deploy_binary; then
        :
    elif deploy_offline; then
        :
    elif deploy_python; then
        :
    else
        echo "❌ 部署失败: 目标机器既无Python 3.9+，也无预编译二进制"
        echo ""
        echo "解决方案:"
        echo "  1. 安装Python: apt install python3 / yum install python3"
        echo "  2. 使用预编译二进制 (需在同架构机器上用 build.sh 打包)"
        exit 1
    fi

    # 验证
    echo ""
    echo "验证安装..."
    if tool --version >/dev/null 2>&1; then
        echo "✅ 部署成功！运行 'tool --help' 查看用法"
    else
        echo "⚠️  安装完成，请重新打开终端后运行 'tool --help'"
    fi
}

main "$@"
