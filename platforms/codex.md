# Codex CLI 适配说明

## 平台信息

- **官方名称**: OpenAI Codex CLI
- **开发者**: OpenAI
- **官方网站**: https://developers.openai.com/codex/cli/
- **产品形态**: 终端 CLI（Rust 编写，开源）+ VS Code/Cursor 扩展 + 桌面 App + 云端 Web
- **安装方式**:
  ```bash
  npm install -g @openai/codex
  # 或
  brew install --cask codex
  # 或
  curl -fsSL https://chatgpt.com/codex/install.sh | sh
  ```

## 技能扩展机制

**原生支持**第三方技能（Agent Skills），基于 "open agent skills standard"。技能 = 含 `SKILL.md` 的目录，可带脚本/引用文件。

### 技能目录

| 作用域 | 路径 |
|--------|------|
| 用户级（跨项目） | `~/.agents/skills/photo-toolbox/` |
| 项目级（仓库根） | `<repo>/.agents/skills/photo-toolbox/` |
| 管理员级 | `/etc/codex/skills/` |

> ⚠️ 目录是 `.agents/skills`，不是 `.codex/skills`（`.codex/` 下只放 `config.toml` 和 `AGENTS.md`）。支持符号链接。

### SKILL.md 格式

- YAML frontmatter **必填字段**: `name`、`description`（仅此两个）
- 同级可放 `scripts/`、`references/`、`assets/`
- 可选旁置文件 `agents/openai.yaml`（**不是 frontmatter**）：控制 UI 显示名/图标、调用策略、MCP 依赖
- 官方**没有** `allowed-tools` 字段（那是 Claude Code 独有）

### 触发方式

- **显式**: 在 prompt 中输入 `$photo-toolbox`，或 TUI 中 `/skills` 选择
- **隐式**: Codex 根据 `description` 自动匹配
- **渐进式披露**: 初始只加载 name/description/路径（≤8000 字符），命中后才读完整 SKILL.md

### 脚本调用

Codex 默认开启 `shell` 工具，SKILL.md 正文中用 `python3 scripts/xxx.py` 指示即可。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本
./install.sh codex

# 方式二: 手动复制
cp -R photo-toolbox/ ~/.agents/skills/photo-toolbox/

# 方式三: 符号链接（开发调试用）
ln -s /path/to/photo-toolbox ~/.agents/skills/photo-toolbox
```

安装后无需重启，在 Codex 对话中直接描述需求即可触发。

## 验证状态

- **文档级验证**: ✅ 已逐页查阅 OpenAI 官方文档（developers.openai.com/codex/cli/）
- **本机实测**: ❌ 未安装 Codex CLI 实测技能加载
- **npm 包**: ✅ 已在线核实 `@openai/codex` 可用

## 官方来源

- Codex CLI 文档: https://developers.openai.com/codex/cli/
- Agent Skills 规范: https://openagentskills.org/（开放标准）
