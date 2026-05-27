#!/bin/bash
# Setup script for 知识库 Skill
# 注册 kwiki MCP 服务到 mcporter

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_URL="https://zhishi.wps.cn/personalwiki/kwiki_mcp/mcp"

echo "🚀 设置 知识库 Skill..."
echo ""

# ============================================================
# 1. 提取版本号
# ============================================================
SKILL_VERSION=""
SKILL_FILE="$PROJECT_ROOT/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
    SKILL_VERSION=$(grep -m1 '^version:' "$SKILL_FILE" | sed 's/^version:[[:space:]]*//')
fi
if [ -z "$SKILL_VERSION" ]; then
    SKILL_VERSION="unknown"
    echo "⚠️  未能从 SKILL.md 提取版本号，将使用 'unknown'"
else
    echo "✅ Skill 版本：$SKILL_VERSION"
fi

# ============================================================
# 2. 确保 mcporter 可用
# ============================================================
echo ""

if ! command -v mcporter &> /dev/null; then
    echo "⚠️  未检测到 mcporter，正在自动安装..."
    if command -v npm &> /dev/null; then
        npm install -g mcporter
        if ! command -v mcporter &> /dev/null; then
            echo "   ❌ mcporter 安装失败，请手动执行：npm install -g mcporter"
            exit 1
        fi
        echo "   ✅ mcporter 安装成功"
    else
        echo "   ❌ 未检测到 npm，无法自动安装 mcporter。"
        echo "   请先安装 Node.js，然后执行：npm install -g mcporter"
        exit 1
    fi
else
    echo "✅ mcporter 已安装"
fi

# ============================================================
# 3. 获取 Token（get-token.sh 会直接写入 mcporter）
# ============================================================
if [ -n "$X_KWIKI_AUTH" ]; then
    echo "✅ 使用环境变量中的 X_KWIKI_AUTH"
    mcporter config add kwiki "$MCP_URL" \
        --header "X-Kwiki-Auth=$X_KWIKI_AUTH" \
        --header "X-Skill-Version=$SKILL_VERSION" \
        --transport http \
        --scope home
    echo "   ✅ mcporter 配置完成"
else
    echo "⚠️  未检测到 X_KWIKI_AUTH，正在通过 get-token.sh 获取..."
    echo ""
    bash "$SCRIPT_DIR/get-token.sh"
    if [ $? -ne 0 ]; then
        echo "❌ 获取 Token 失败，请手动运行：bash scripts/get-token.sh"
        exit 1
    fi
fi

# ============================================================
# 4. 验证
# ============================================================
echo ""
echo "🧪 验证配置..."
if mcporter list kwiki > /dev/null 2>&1; then
    echo "✅ 配置验证成功！"
    echo ""
    mcporter list kwiki || true
else
    echo "⚠️  配置已写入，但连通性验证失败。请检查网络或 Token。"
    echo ""
fi

# ============================================================
# 5. 启动 Token 保活
# ============================================================
echo ""
echo "🔄 启动 Token 保活进程..."
bash "$SCRIPT_DIR/get-token.sh" --keepalive 300 &
KEEPALIVE_PID=$!
disown "$KEEPALIVE_PID" 2>/dev/null
echo "   ✅ 保活进程已启动（PID: $KEEPALIVE_PID，间隔 5 分钟）"

echo ""
echo "─────────────────────────────────────"
echo "🎉 设置完成！"
echo ""
echo "🏠 kwiki 主页：https://zhishi.wps.cn"
echo "📖 更多信息请查看 SKILL.md"
echo ""
echo "💡 Token 管理："
echo "   检查 token:    bash scripts/get-token.sh --check"
echo "   停止保活:      bash scripts/get-token.sh --stop-keepalive"
echo "   手动保活:      bash scripts/get-token.sh --keepalive [间隔秒]"
