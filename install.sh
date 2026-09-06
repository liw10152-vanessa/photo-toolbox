#!/usr/bin/env bash
# photo-toolbox 多平台安装脚本
# 将本技能安装到指定 AI Agent 平台的技能目录。
# 用法: ./install.sh <平台名> [--link]
#   平台名: codex | claude-code | kimi | doubao | marvis | workbuddy | all
#   --link: 使用符号链接而非复制（修改源文件即时生效）
#
# 示例:
#   ./install.sh codex              # 安装到 Codex CLI
#   ./install.sh claude-code --link # 符号链接到 Claude Code
#   ./install.sh all                # 安装到所有支持的平台

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="photo-toolbox"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# 解析参数
USE_LINK=false
TARGET=""

for arg in "$@"; do
  case "$arg" in
    --link) USE_LINK=true ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *)
      if [ -z "$TARGET" ]; then
        TARGET="$arg"
      else
        error "多余参数: $arg"
        exit 1
      fi
      ;;
  esac
done

if [ -z "$TARGET" ]; then
  error "请指定平台名。用法: ./install.sh <codex|claude-code|kimi|doubao|marvis|workbuddy|all>"
  exit 1
fi

# 安装函数: install_skill <目标目录>
install_skill() {
  local dest_dir="$1"
  local dest_path="${dest_dir}/${SKILL_NAME}"

  mkdir -p "$dest_dir"

  # 如果已存在，先移除（符号链接或目录）
  if [ -L "$dest_path" ] || [ -d "$dest_path" ]; then
    warn "已存在 ${dest_path}，将覆盖..."
    rm -rf "$dest_path"
  fi

  if [ "$USE_LINK" = true ]; then
    ln -s "$SCRIPT_DIR" "$dest_path"
    info "符号链接已创建: ${dest_path} -> ${SCRIPT_DIR}"
  else
    cp -R "$SCRIPT_DIR" "$dest_path"
    # 复制后移除 .git 目录（如果有）
    rm -rf "${dest_path}/.git"
    info "已复制到: ${dest_path}"
  fi
}

# 各平台目标目录定义
# 注意: 路径均基于官方文档或开发者实测确认，详见 platforms/ 目录下各平台文档。

install_codex() {
  # OpenAI Codex CLI: 用户级技能目录 ~/.agents/skills/
  # 官方文档: https://developers.openai.com/codex/cli/
  local dest="${HOME}/.agents/skills"
  info "安装到 OpenAI Codex CLI..."
  install_skill "$dest"
  info "完成。在 Codex 中用 \$photo-toolbox 显式调用，或描述需求自动触发。"
}

install_claude_code() {
  # Anthropic Claude Code: 用户级技能目录 ~/.claude/skills/
  # 官方文档: https://docs.claude.com/en/docs/claude-code/overview
  local dest="${HOME}/.claude/skills"
  info "安装到 Anthropic Claude Code..."
  install_skill "$dest"
  info "完成。Claude Code 会根据 description 自动调用此技能。"
}

install_kimi() {
  # Kimi Code CLI: 技能目录 ~/.kimi-code/skills/ （路径待官方确认，同时安装到 ~/.agents/skills/ 兼容）
  # 官方文档: https://www.kimi.com/code/docs/
  local dest1="${HOME}/.kimi-code/skills"
  local dest2="${HOME}/.agents/skills"
  info "安装到 Kimi Code CLI..."
  install_skill "$dest1"
  info "同时安装到 ${dest2}（跨工具共享目录，提高被扫描到的概率）..."
  install_skill "$dest2"
  warn "Kimi Code 技能目录路径尚未从官方文档原文确认，建议安装后运行 'ls ~/.kimi-code/' 验证。"
  info "如 Kimi Code 未自动识别，可在对话中直接引用脚本路径执行。"
}

install_doubao() {
  # 豆包工作电脑版: 技能目录在 workspace/.user_skills/ 下
  # 路径因操作系统和安装环境而异，此处尝试自动检测
  info "安装到 豆包工作电脑版..."

  # 尝试常见路径
  local candidates=(
    "${HOME}/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills"
    "${HOME}/.doubao/agent_mode/workspace/.user_skills"
    "${APPDATA:-}/Doubao/Default/.doubao/agent_mode/workspace/.user_skills"
  )

  local dest=""
  for candidate in "${candidates[@]}"; do
    if [ -n "$candidate" ] && [ -d "$(dirname "$candidate")" ]; then
      dest="$candidate"
      break
    fi
  done

  if [ -z "$dest" ]; then
    # 回退到 macOS 默认路径
    dest="${HOME}/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills"
    warn "未检测到豆包工作目录，使用默认路径: ${dest}"
  fi

  install_skill "$dest"
  info "完成。重启豆包工作电脑版后生效。"
  warn "豆包工作 frontmatter 仅允许 name 和 description 字段，当前 SKILL.md 已符合规范。"
}

install_marvis() {
  # 腾讯 Marvis: 技能目录 ~/.marvis/skills/
  # 官网: https://marvis.qq.com/
  local dest="${HOME}/.marvis/skills"
  info "安装到 腾讯 Marvis..."
  install_skill "$dest"
  info "完成。在 Marvis 对话中说'帮我处理图片'或 @photo-toolbox 触发。"
  warn "Marvis 技能目录路径来自第三方开发者实测文章，非官方文档直接确认。"
}

install_workbuddy() {
  # 腾讯 WorkBuddy: 三级技能目录，用户全局 ~/.workbuddy/skills/
  # 官网: https://www.workbuddy.cn/  开放平台: https://open.workbuddy.cn/
  local dest="${HOME}/.workbuddy/skills"
  info "安装到 腾讯 WorkBuddy..."
  install_skill "$dest"
  info "完成。重启 WorkBuddy 后自动识别。"
  info "也可安装到项目级: .agents/skills/ 或工作区级: skills/"
}

# 主逻辑
case "$TARGET" in
  codex)       install_codex ;;
  claude-code) install_claude_code ;;
  kimi)        install_kimi ;;
  doubao)      install_doubao ;;
  marvis)      install_marvis ;;
  workbuddy)   install_workbuddy ;;
  all)
    info "安装到所有支持的平台..."
    install_codex
    echo
    install_claude_code
    echo
    install_kimi
    echo
    install_doubao
    echo
    install_marvis
    echo
    install_workbuddy
    echo
    info "全部平台安装完成！"
    ;;
  *)
    error "未知平台: ${TARGET}"
    error "支持的平台: codex, claude-code, kimi, doubao, marvis, workbuddy, all"
    exit 1
    ;;
esac

echo
info "安装后请确保 Python 依赖已安装:"
echo "  pip3 install pillow reportlab python-docx"
