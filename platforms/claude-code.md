# Claude Code 适配说明

## 平台信息

- **官方名称**: Claude Code
- **开发者**: Anthropic
- **官方网站**: https://docs.claude.com/en/docs/claude-code/overview
- **产品形态**: 终端 CLI + VS Code/JetBrains 扩展 + 桌面 App + Web
- **安装方式**:
  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  # 或
  brew install --cask claude-code
  # 或（npm 仍可用）
  npm install -g @anthropic-ai/claude-code
  ```

## 技能扩展机制

**原生支持**第三方技能（Agent Skills）。SKILL.md + 可选脚本/模板/引用文件，支持团队经 git 共享。

### 技能目录

| 作用域 | 路径 |
|--------|------|
| 用户级（跨项目） | `~/.claude/skills/photo-toolbox/SKILL.md` |
| 项目级（随 git 共享） | `.claude/skills/photo-toolbox/SKILL.md` |
| 插件级 | 随已装 plugin 自动提供 |

> ⚠️ 与 Codex 不同，这里是 `.claude/skills`（不是 `.agents/skills`）。

### SKILL.md 格式

- YAML frontmatter **必填字段**:
  - `name`: 仅小写字母/数字/连字符，≤64 字符
  - `description`: 做什么 + 何时触发，≤1024 字符（决定自动命中）
- **可选字段**（Claude Code 独有）:
  - `allowed-tools`: 如 `Read, Grep, Glob`，限定该 skill 激活时免审批可用的工具集
- 同级目录: `scripts/`、`templates/`、`reference.md` 等

> 💡 photo-toolbox 当前 SKILL.md 仅含 name+description，已符合规范且跨平台通用。如需添加 `allowed-tools` 请创建 Claude Code 专属版本，因为豆包工作不允许额外字段。

### 触发方式

- **模型自动调用（model-invoked）**: Claude 根据 description 自行决定何时使用——无显式斜杠
- 区别于斜杠命令（user-invoked，需手打 `/命令`）
- **渐进式披露**: supporting files 仅在需要时读取

### 脚本调用

SKILL.md 正文用 `python3 scripts/xxx.py` 指示。官方明确"Claude 会按需自动安装依赖（或请求许可）"。脚本需 `chmod +x`，路径用正斜杠。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本
./install.sh claude-code

# 方式二: 手动复制
cp -R photo-toolbox/ ~/.claude/skills/photo-toolbox/

# 方式三: 符号链接（开发调试用）
ln -s /path/to/photo-toolbox ~/.claude/skills/photo-toolbox
```

## 验证状态

- **文档级验证**: ✅ 已逐页查阅 Anthropic 官方文档（docs.claude.com）
- **本机实测**: ❌ 未安装 Claude Code 实测技能加载
- **npm 包**: ✅ 已在线核实 `@anthropic-ai/claude-code` 可用

## 补充: CLAUDE.md 机制

除 Skills 外，Claude Code 还支持 CLAUDE.md 指令文件（四层优先级）:
- 企业级: `/Library/Application Support/ClaudeCode/CLAUDE.md`
- 项目级: `./CLAUDE.md` 或 `./.claude/CLAUDE.md`
- 用户级: `~/.claude/CLAUDE.md`

如不使用 Skills 机制，也可将 photo-toolbox 的使用说明写入项目级 CLAUDE.md。

## 官方来源

- Claude Code 概览: https://docs.claude.com/en/docs/claude-code/overview
- Agent Skills: https://docs.claude.com/en/docs/claude-code/skills
- CLAUDE.md: https://docs.claude.com/en/docs/claude-code/claude-md
