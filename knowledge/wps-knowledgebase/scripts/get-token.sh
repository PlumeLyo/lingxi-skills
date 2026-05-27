#!/bin/bash
#
# kwiki 授权工具 - 获取 skills_hub token
#
# 流程：
#   1. 调用服务端接口生成授权码 code
#   2. 构造回调 URL，拼接登录链接
#   3. 用户在浏览器打开链接登录
#   4. 登录成功后服务端回调，本脚本轮询 exchange 接口获取 token
#
# 用法：
#   bash get-token.sh [--json] [--notify]   # 获取新 token
#   bash get-token.sh --check                # 检查当前 token 有效性
#   bash get-token.sh --keepalive [间隔秒]   # 后台心跳保活（默认 300s）
#
# 特性：
#   - 首次超时自动重试一次（共两轮，每轮 2 分钟）
#   - 第二次仍超时则检查 API 可用性并输出诊断信息
#   - 轮询间隔 10 秒
#   - --check 模式查询 token 剩余有效期
#   - --keepalive 模式定期心跳续期，token 失效时输出告警

BASE_URL="https://zhishi.wps.cn"
_TMPDIR="${TMPDIR:-/tmp}"

open_url_in_browser() {
  local url="$1"

  # macOS
  if command -v open &>/dev/null && [[ "$(uname)" == "Darwin" ]]; then
    open "$url" && return 0
  fi

  # Linux desktop
  if command -v xdg-open &>/dev/null; then
    xdg-open "$url" 2>/dev/null && return 0
  fi

  # Windows: PowerShell — 对含 & ? = 等特殊字符的 URL 最可靠
  if command -v powershell.exe &>/dev/null; then
    powershell.exe -NoProfile -Command "Start-Process '${url}'" 2>/dev/null && return 0
  fi

  # Windows: rundll32 — 系统自带，不依赖 shell 引号解析
  if command -v rundll32.exe &>/dev/null; then
    rundll32.exe url.dll,FileProtocolHandler "$url" 2>/dev/null && return 0
  fi

  # Windows: cmd.exe /c start (Git Bash / MSYS2)
  if command -v cmd.exe &>/dev/null; then
    cmd.exe /c start "" "$url" 2>/dev/null && return 0
  fi

  # WSL
  if command -v wslview &>/dev/null; then
    wslview "$url" 2>/dev/null && return 0
  fi

  # Windows: explorer.exe 兜底
  if command -v explorer.exe &>/dev/null; then
    explorer.exe "$url" 2>/dev/null && return 0
  fi

  # 跨平台兜底：python webbrowser 模块
  if command -v python3 &>/dev/null; then
    python3 -c "import webbrowser; webbrowser.open('$url')" 2>/dev/null && return 0
  elif command -v python &>/dev/null; then
    python -c "import webbrowser; webbrowser.open('$url')" 2>/dev/null && return 0
  fi

  echo "⚠️  无法自动打开浏览器，请手动复制上方链接到浏览器中打开"
  return 1
}

urlencode() {
  local string="$1"
  python3 -c "import urllib.parse; print(urllib.parse.quote('$string', safe=''))" 2>/dev/null ||
  python -c "import urllib.parse; print(urllib.parse.quote('$string', safe=''))" 2>/dev/null ||
  echo "$string" | sed \
    -e 's/%/%25/g' \
    -e 's/ /%20/g' \
    -e 's/:/%3A/g' \
    -e 's/\//%2F/g' \
    -e 's/?/%3F/g' \
    -e 's/=/%3D/g' \
    -e 's/&/%26/g' \
    -e 's/#/%23/g'
}

extract_json_value() {
  local json="$1" key="$2"
  if command -v jq &>/dev/null; then
    local value=$(echo "$json" | jq -r ".data.$key // .$key // empty" 2>/dev/null)
    if [ -n "$value" ] && [ "$value" != "null" ]; then
      echo "$value"
    return
    fi
  fi
  # jq unavailable — grep fallback, tail to prefer nested data.key over top-level key
  echo "$json" | grep -o "\"${key}\":[^,}]*" | tail -1 | sed "s/\"${key}\"://; s/\"//g; s/ //g"
}

send_notify() {
  local message="$1"
  if echo "$@" | grep -q "\-\-notify"; then
    if command -v openclaw &>/dev/null; then
      openclaw agent --message "🔑 kwiki Token 获取成功！$message" 2>/dev/null || true
    fi
    if command -v osascript &>/dev/null; then
      osascript -e "display notification \"$message\" with title \"kwiki Token 已获取\"" 2>/dev/null || true
    fi
  fi
}

save_token() {
  local token="$1" expires="$2"
  local MCP_URL="https://zhishi.wps.cn/personalwiki/kwiki_mcp/mcp"

  export X_KWIKI_AUTH="${token}"

  # 提取版本号
  local SKILL_FILE
  SKILL_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/SKILL.md"
  local skill_version="unknown"
  if [ -f "$SKILL_FILE" ]; then
    skill_version=$(grep -m1 '^version:' "$SKILL_FILE" | sed 's/^version:[[:space:]]*//')
  fi

  if command -v mcporter &> /dev/null; then
    mcporter config add kwiki "$MCP_URL" \
      --header "X-Kwiki-Auth=$token" \
      --header "X-Skill-Version=$skill_version" \
      --transport http \
      --scope home 2>/dev/null
    echo "📝 Token 已写入 mcporter（kwiki）"
  else
    echo "⚠️  mcporter 未安装，Token 仅在当前会话有效（X_KWIKI_AUTH）"
    echo "   运行 bash scripts/setup.sh 可自动安装 mcporter 并持久化 Token"
  fi
}

check_token() {
  local token=""

  if [ -n "$X_KWIKI_AUTH" ]; then
    token="$X_KWIKI_AUTH"
  fi

  if [ -z "$token" ]; then
    echo "❌ 未找到 token，请先运行 bash get-token.sh 获取"
    return 1
  fi

  local tmp_file="${_TMPDIR}/kwiki_check_$$.json"
  local http_code
  http_code=$(curl -s -o "$tmp_file" -w '%{http_code}' \
    -H "X-Kwiki-Auth: ${token}" \
    "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/info")
  local response=$(cat "$tmp_file" 2>/dev/null)
  rm -f "$tmp_file"

  if [ "$http_code" = "200" ]; then
    local expires=$(extract_json_value "$response" "expires_in")
    if [ -n "$expires" ] && [ "$expires" != "null" ] && [ "$expires" -gt 0 ] 2>/dev/null; then
      local days=$((expires / 86400))
      local hours=$(( (expires % 86400) / 3600 ))
      echo "✅ Token 有效"
      echo "   剩余有效期: ${days} 天 ${hours} 小时（${expires}s）"
      return 0
    fi
  fi

  echo "❌ Token 已失效或无效（HTTP ${http_code}）"
  echo "   请重新运行 bash get-token.sh 获取"
  return 1
}

keepalive() {
  local interval="${1:-300}"
  local pid_file="${_TMPDIR}/kwiki_keepalive.pid"

  # 检查是否已有保活进程在运行
  if [ -f "$pid_file" ]; then
    local old_pid
    old_pid=$(cat "$pid_file" 2>/dev/null)
    if kill -0 "$old_pid" 2>/dev/null; then
      echo "保活进程已在运行 (PID: $old_pid)，先终止旧进程"
      kill "$old_pid" 2>/dev/null
      sleep 1
    fi
    rm -f "$pid_file"
  fi

  local token=""
  if [ -n "$X_KWIKI_AUTH" ]; then
    token="$X_KWIKI_AUTH"
  fi

  if [ -z "$token" ]; then
    echo "❌ 未找到 token（X_KWIKI_AUTH 环境变量为空），无法启动保活"
    return 1
  fi

  echo "🔄 启动 token 保活（间隔 ${interval}s，PID: $$）"
  echo $$ > "$pid_file"

  trap 'rm -f "$pid_file"; echo ""; echo "保活进程已停止"; exit 0' INT TERM

  local fail_count=0
  while true; do
    sleep "$interval"

    local tmp_file="${_TMPDIR}/kwiki_ka_$$.json"
    local http_code
    http_code=$(curl -s -o "$tmp_file" -w '%{http_code}' \
      -H "X-Kwiki-Auth: ${token}" \
      "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/info")
    local response=$(cat "$tmp_file" 2>/dev/null)
    rm -f "$tmp_file"

    if [ "$http_code" = "200" ]; then
      local expires=$(extract_json_value "$response" "expires_in")
      if [ -n "$expires" ] && [ "$expires" != "null" ] && [ "$expires" -gt 0 ] 2>/dev/null; then
        fail_count=0
        local days=$((expires / 86400))
        local hours=$(( (expires % 86400) / 3600 ))
        echo "[$(date '+%H:%M:%S')] ✅ 心跳成功，剩余 ${days}d${hours}h"
        continue
      fi
    fi

    fail_count=$((fail_count + 1))
    echo "[$(date '+%H:%M:%S')] ⚠️  心跳失败（HTTP ${http_code}，连续 ${fail_count} 次）"

    if [ "$fail_count" -ge 3 ]; then
      echo "[$(date '+%H:%M:%S')] ❌ 连续 3 次心跳失败，token 可能已失效"
      echo "   请重新运行 bash get-token.sh 获取新 token"
      rm -f "$pid_file"
      return 1
    fi
  done
}

stop_keepalive() {
  local pid_file="${_TMPDIR}/kwiki_keepalive.pid"
  if [ -f "$pid_file" ]; then
    local pid
    pid=$(cat "$pid_file" 2>/dev/null)
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      echo "已停止保活进程 (PID: $pid)"
    else
      echo "保活进程 (PID: $pid) 已不存在"
    fi
    rm -f "$pid_file"
  else
    echo "没有运行中的保活进程"
  fi
}

check_api_health() {
  echo ""
  echo "🔍 正在检查 API 可用性..."

  local http_code
  http_code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/code/generate")
  if [ "$http_code" = "200" ]; then
    echo "✅ generate 接口正常（HTTP ${http_code}）"
  else
    echo "❌ generate 接口异常（HTTP ${http_code}）"
  fi

  http_code=$(curl -s -o /dev/null -w '%{http_code}' -X POST \
    "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/exchange" \
    -H "Content-Type: application/json" \
    -d '{"code": "test_invalid_code"}')
  if [ "$http_code" = "400" ] || [ "$http_code" = "200" ] || [ "$http_code" = "202" ]; then
    echo "✅ exchange 接口可达（HTTP ${http_code}）"
  else
    echo "❌ exchange 接口异常（HTTP ${http_code}），可能是网络或服务端问题"
  fi
}

generate_code() {
  local tmp_file="${_TMPDIR}/kwiki_generate_$$.json"
  local http_code
  http_code=$(curl -s -o "$tmp_file" -w '%{http_code}' -X POST "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/code/generate")
  local response=$(cat "$tmp_file" 2>/dev/null)
  rm -f "$tmp_file"

  local code_value=$(extract_json_value "$response" "code")

  if [ "$http_code" = "200" ] && [ -n "$code_value" ] && [ ${#code_value} -ge 16 ]; then
    echo "$code_value"
    return 0
  else
    echo "[ERROR] HTTP=${http_code}, body=${response}" >&2
    return 1
  fi
}

poll_for_token() {
  local code="$1"
  local timeout="${2:-300}"
  local interval=10
  local start=$(date +%s)
  local last_dot=0

  while true; do
    local now=$(date +%s)
    local elapsed=$((now - start))

    if [ "$elapsed" -ge "$timeout" ]; then
      return 1
    fi

    local tmp_file="${_TMPDIR}/kwiki_exchange_$$.json"
    local http_code
    http_code=$(curl -s -o "$tmp_file" -w '%{http_code}' -X POST \
      "${BASE_URL}/kwiki/api/v1/skills_hub/access_token/exchange" \
      -H "Content-Type: application/json" \
      -d "{\"code\": \"${code}\"}")
    local response=$(cat "$tmp_file" 2>/dev/null)
    rm -f "$tmp_file"

    local token=$(extract_json_value "$response" "access_token")
    local expires=$(extract_json_value "$response" "expires_in")
    local resp_code=$(extract_json_value "$response" "code")

    if [ "$http_code" = "200" ] && [ -n "$token" ] && [ "$token" != "null" ] && [ ${#token} -gt 10 ]; then
      echo ""
      echo ""
      echo "✅ 登录成功！"
      echo ""
      echo "======================================================================"
      echo "  授权信息"
      echo "======================================================================"
      echo ""
      echo "🔑 X-Kwiki-Auth (access_token):"
      echo "${token}"
      echo ""
      echo "⏰ expires_in: ${expires}s (约 $((expires / 86400)) 天)"
      echo ""
      echo "======================================================================"
      echo ""

      save_token "$token" "$expires"

      local token_short="${token:0:20}..."
      send_notify "Token: ${token_short}, 有效期：$((expires / 86400))天"

      if echo "$@" | grep -q "\-\-json"; then
        echo "{\"token\":\"${token}\",\"expires_in\":${expires}}"
      fi
      return 0

    elif [ "$resp_code" = "202" ]; then
      if [ $((elapsed % 5)) -eq 0 ] && [ "$elapsed" -ne "$last_dot" ]; then
        printf "."
        last_dot=$elapsed
      fi
    elif [ "$http_code" = "400" ]; then
      echo ""
      echo "❌ 授权码无效或已过期"
      return 2
    else
      echo ""
      echo "[DEBUG] HTTP=${http_code}, body=${response}"
    fi

    sleep $interval
  done
}

# ============================================================
# 主流程
# ============================================================

run_auth_round() {
  local round="$1"

  echo ""
  echo "======================================================================"
  if [ "$round" -gt 1 ]; then
    echo "  kwiki 授权 - 第 ${round} 次尝试"
  else
    echo "  kwiki 授权 - 获取 skills_hub token"
  fi
  echo "======================================================================"
  echo ""
  echo "⏳ 正在生成授权码..."

  CODE=$(generate_code)
  if [ $? -ne 0 ]; then
    echo "❌ 生成授权码失败"
    echo "$CODE"
    return 1
  fi

  echo "✅ 授权码已生成（有效期 10 分钟）"
  echo ""

  CB="${BASE_URL}/kwiki/api/v1/skills_hub/callback?code=${CODE}"
  ENCODED_CB=$(urlencode "$CB")
  LOGIN_URL="https://account.wps.cn/login?cb=${ENCODED_CB}"

  echo "======================================================================"
  echo "  WPS 授权 - 获取 Token"
  echo "======================================================================"
  echo ""
  echo "  请在浏览器中打开以下链接登录："
  echo ""
  echo "  ${LOGIN_URL}"
  echo ""
  echo "======================================================================"
  echo ""

  # 自动打开浏览器（兼容 macOS / Linux / Windows Git Bash / MSYS2 / WSL）
  open_url_in_browser "${LOGIN_URL}"

  echo "⏳ 正在等待您完成授权，无需任何额外操作..."
  echo " （最多等待 2 分钟）"
  echo ""
  echo ""

  poll_for_token "$CODE" 120 "$@"
  return $?
}

# --check 模式：仅检查 token 有效性
if echo "$@" | grep -q "\-\-check"; then
  check_token
  exit $?
fi

# --stop-keepalive 模式：停止保活进程
if echo "$@" | grep -q "\-\-stop-keepalive"; then
  stop_keepalive
  exit $?
fi

# --keepalive 模式：后台心跳保活
if echo "$@" | grep -q "\-\-keepalive"; then
  INTERVAL="300"
  for arg in "$@"; do
    if [ "$prev_arg" = "--keepalive" ] && echo "$arg" | grep -qE '^[0-9]+$'; then
      INTERVAL="$arg"
    fi
    prev_arg="$arg"
  done
  keepalive "$INTERVAL"
  exit $?
fi

# 第一轮
run_auth_round 1 "$@"
RESULT=$?

if [ $RESULT -eq 0 ]; then
  exit 0
fi

if [ $RESULT -eq 2 ]; then
  echo "授权码已失效，请重新运行脚本"
  exit 1
fi

# 第一轮超时，自动重试
echo ""
echo ""
echo "⚠️  第一次尝试超时（2 分钟），自动发起第二次尝试..."
echo ""

run_auth_round 2 "$@"
RESULT=$?

if [ $RESULT -eq 0 ]; then
  exit 0
fi

# 两轮都超时，检查 API 可用性
echo ""
echo ""
echo "❌ 两次尝试均超时，正在诊断问题..."
check_api_health
echo ""
echo "💡 建议："
echo "   1. 确认网络可正常访问 ${BASE_URL}"
echo "   2. 在浏览器打开登录链接后，确保完成了 WPS 账号登录"
echo "   3. 如果已登录但页面无跳转，可能是回调地址异常，请联系管理员"
echo ""
exit 1
