# 多平台适配文档

photo-toolbox 支持以下 6 个 AI Agent 平台。所有平台均使用 `SKILL.md` + YAML frontmatter（name + description）格式，趋于统一的 "open agent skills standard"。

## 平台一览

| 平台 | 开发者 | 原生技能 | 用户级安装目录 | 验证状态 | 详细文档 |
|------|--------|---------|--------------|---------|---------|
| **Codex CLI** | OpenAI | ✅ | `~/.agents/skills/` | 文档级(官方) | [codex.md](codex.md) |
| **Claude Code** | Anthropic | ✅ | `~/.claude/skills/` | 文档级(官方) | [claude-code.md](claude-code.md) |
| **Kimi Code** | 月之暗面 | ✅ | `~/.kimi-code/skills/` ⚠️ | 文档级(路径推测) | [kimi.md](kimi.md) |
| **豆包工作** | 字节跳动 | ✅ | `.user_skills/`(workspace下) | ✅ 已实测 | [doubao.md](doubao.md) |
| **Marvis** | 腾讯应用宝 | ✅ | `~/.marvis/skills/` | 文档级(第三方) | [marvis.md](marvis.md) |
| **WorkBuddy** | 腾讯云 CodeBuddy | ✅ | `~/.workbuddy/skills/` | 文档级(腾讯云文档) | [workbuddy.md](workbuddy.md) |

## 快速安装

```bash
# 安装到指定平台
./install.sh codex
./install.sh claude-code
./install.sh kimi
./install.sh doubao
./install.sh marvis
./install.sh workbuddy

# 一键安装到所有平台
./install.sh all

# 使用符号链接（开发调试，修改即时生效）
./install.sh codex --link
```

## 兼容性说明

- **SKILL.md frontmatter**: 所有平台均支持 `name` + `description` 两个必填字段。当前 photo-toolbox 的 SKILL.md 仅含这两个字段，**天然兼容所有平台**。
- **豆包限制**: 豆包工作官方明确"Do not include any other fields in YAML frontmatter"，因此根目录 SKILL.md 不添加 `allowed-tools` 等平台专属字段。
- **Claude Code 专属**: 如需使用 `allowed-tools` 字段，请创建 Claude Code 专属版本，不要修改根目录 SKILL.md。
- **Codex 专属**: 如需配置 UI 显示名/图标/MCP 依赖，请创建旁置文件 `agents/openai.yaml`，不要修改 SKILL.md frontmatter。
- **scripts/ 层**: 4 个 Python 脚本与平台无关，所有平台均通过 `python3 scripts/xxx.py` 调用。

## 验证状态说明

| 验证等级 | 含义 |
|---------|------|
| ✅ 已实测 | 在本机实际安装并运行通过 |
| 文档级(官方) | 查阅了平台官方文档确认机制，但未本机实测 |
| 文档级(第三方) | 机制信息来自第三方开发者文章，非官方文档直接确认 |
| ⚠️ 路径推测 | 机制存在但具体目录路径未从官方文档确认，需实测验证 |

## 局限与风险

1. **Kimi Code 技能目录路径未确认**: 官方文档站为 JS 渲染，外部抓取失败。建议安装后 `ls ~/.kimi-code/` 实测。
2. **Marvis 技能机制透明度较低**: 信息来自第三方开发者文章，建议安装后实测确认。
3. **豆包以外平台的首次引导机制**: photo-toolbox 的首次使用引导（user-preferences.json）依赖 Agent 读取 SKILL.md 正文并遵循指令。在其他平台上理论上有效，但未实测验证。
4. **交付工具差异**: 豆包工作使用 `present_files` 交付产物，其他平台可能使用不同的交付机制，需相应调整。
