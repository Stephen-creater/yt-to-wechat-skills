#!/usr/bin/env bash
# 把 skills/ 下的 7 个 skill 软链接到 Claude Code 或 Codex 的 skills 目录。
# 软链接的好处：你改了 SKILL.md，下次跑就生效，不用重装。
#
# 用法：
#   bash INSTALL.sh            # 交互式
#   bash INSTALL.sh claude     # 只装 Claude Code
#   bash INSTALL.sh codex      # 只装 Codex
#   bash INSTALL.sh both       # 两个都装
#   bash INSTALL.sh --copy …   # 用 cp -R 代替 ln -s（不会跟着源更新）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "ERROR: 找不到 $SKILLS_SRC"
  exit 1
fi

# 解析参数
MODE="link"
TARGET=""
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    claude|codex|both) TARGET="$arg" ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
  esac
done

# 没指定目标就问
if [ -z "$TARGET" ]; then
  echo "装到哪里？"
  echo "  1) Claude Code (~/.claude/skills/)"
  echo "  2) Codex       (~/.codex/skills/)"
  echo "  3) 都装"
  read -rp "选择 [1/2/3]: " choice
  case "$choice" in
    1) TARGET="claude" ;;
    2) TARGET="codex" ;;
    3) TARGET="both" ;;
    *) echo "无效选择"; exit 1 ;;
  esac
fi

install_to() {
  local dest="$1"
  mkdir -p "$dest"
  echo ""
  echo "▶ 安装到 $dest"
  for skill_dir in "$SKILLS_SRC"/*/; do
    name="$(basename "$skill_dir")"
    target="$dest/$name"
    if [ -e "$target" ] || [ -L "$target" ]; then
      echo "  ⚠ $name 已存在，跳过（要更新先手动删 $target）"
      continue
    fi
    if [ "$MODE" = "copy" ]; then
      cp -R "$skill_dir" "$target"
      echo "  ✓ 复制 $name"
    else
      ln -s "$skill_dir" "$target"
      echo "  ✓ 链接 $name"
    fi
  done
}

case "$TARGET" in
  claude) install_to "$HOME/.claude/skills" ;;
  codex)  install_to "$HOME/.codex/skills" ;;
  both)
    install_to "$HOME/.claude/skills"
    install_to "$HOME/.codex/skills"
    ;;
esac

echo ""
echo "✅ Skill 安装完成。"
echo ""
echo "下一步：配置密钥"
echo "  1) 选一个目录作为「写作项目根目录」（可以是空的新目录）"
echo "  2) 在该目录下建 .ds-skills/，按 README.md「三、配置密钥」复制模板并填值"
echo "  3) 进到该目录里打开 Claude Code / Codex，对它说："
echo "       帮我把这个 YouTube 写成公众号草稿：<YouTube URL>"
echo ""
