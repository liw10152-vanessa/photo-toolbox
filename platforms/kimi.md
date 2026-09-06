# Kimi 适配说明

## 平台信息

- **官方名称**: Kimi（月之暗面 Moonshot AI）
- **开发者**: 月之暗面
- **官方网站**: https://kimi.com
- **Kimi Code CLI**: https://code.kimi.com
- **产品形态**:

| 形态 | 说明 | 技能支持 |
|------|------|---------|
| Kimi 网页版 / App | 消费级聊天助手 | ❌ 无本地技能 |
| Kimi Agent 模式 | 深度任务 Agent（K2.6 起） | ⚠️ 云端 UI 式技能，无法跑本地脚本 |
| **Kimi Work 桌面端** | 桌面端本地 Agent（Mac/Win） | ⚠️ 应用内创建技能，无公开目录规范 |
| **Kimi Code CLI** | 终端编程 Agent | ✅ 本地文件式技能（最兼容） |
| Kimi 开放平台 | 模型 API | ❌ 纯 API，无 Skill 托管 |

## Kimi Code CLI 技能扩展机制

**原生支持**本地 Skills 和自定义 Agent 文件。

### 安装 Kimi Code CLI

```bash
curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
# 或
brew install kimi-code
```

### Agent 文件机制（官方文档已确认）

这是与 photo-toolbox 结构最接近的机制:

- **存放目录**（优先级: 显式 `--agent-file` > 项目级 > Extra > 用户级 > 插件级 > 内置）:
  - 用户级: `~/.kimi-code/agents/`、`~/.agents/agents/`（跨工具共享约定）
  - 项目级: `.kimi-code/agents/`、`.agents/agents/`
- **文件格式**: Markdown + YAML frontmatter
- **frontmatter 字段**:
  - `description`（**必填**，主代理据此决定何时派生）
  - `name`（可选，kebab-case，缺省取文件名）
  - `whenToUse` / `override` / `model_preference` / `tools` / `disallowedTools` / `subagents`
- **触发方式**: 主代理自动发现并按 description 派生为子代理；也可 `kimi --agent <name>` 作主代理启动

### Skills 机制（本地 SKILL.md 目录）

机制存在，但**精确目录未能从官方文档原文确认**（文档站为 JS 渲染，外部抓取失败）:

- 官方文档确认 CLI 会注入"合并后的 Agent Skills"且子代理可调用 Skill
- 按业界收敛约定，Skills 对应位置应为:
  - `~/.kimi-code/skills/photo-toolbox/`
  - `~/.agents/skills/photo-toolbox/`（跨工具共享）
  - 项目级 `.agents/skills/photo-toolbox/`
- **状态: 文档级验证（机制存在）+ 推测（具体路径）**

### 脚本调用

Agent 拥有 Bash/Read/Write 等工具，直接在终端执行 `python3 <skill>/scripts/xxx.py`（与豆包工作完全同构）。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本（同时安装到两个目录提高兼容性）
./install.sh kimi

# 方式二: 手动复制
cp -R photo-toolbox/ ~/.kimi-code/skills/photo-toolbox/
cp -R photo-toolbox/ ~/.agents/skills/photo-toolbox/

# 方式三: 作为 Agent 文件安装
cp photo-toolbox/SKILL.md ~/.kimi-code/agents/photo-toolbox.md
```

安装后建议验证:
```bash
ls ~/.kimi-code/
# 确认 skills 目录是否存在及被 CLI 扫描
```

## Kimi Work 桌面端适配

Kimi Work 能读写本地文件，但**无公开的本地技能目录规范**。适配方式:
1. 在 Kimi Work 中通过"创建技能"功能，将 photo-toolbox 的 SKILL.md 正文作为工作流说明录入
2. 在技能说明中写明脚本路径: `python3 /path/to/photo-toolbox/scripts/xxx.py`
3. 属于"产品内功能适配"而非标准技能文件安装

## Kimi 网页版 Agent 模式

⚠️ **不适用**: Kimi 网页版跑在云端，无法直接执行你电脑上的 Python 脚本。即使通过"/创建技能"录入 SKILL.md，也无法调用本地 scripts/。

## 验证状态

- **文档级验证**: ✅ Kimi Code Agent 文件机制已从官方文档确认
- **Skills 目录路径**: ⚠️ 推测（官方文档站 JS 渲染导致外部抓取失败）
- **本机实测**: ❌ 未安装 Kimi Code CLI 实测
- **建议**: 安装 Kimi Code CLI 后用 `/help` 或 `ls ~/.kimi-code/` 实际目录做一次实测确认

## 官方来源

- Kimi Code 概览: https://www.kimi.com/code/docs/
- Kimi Work 发布: http://news.qq.com/rain/a/20260604A07RSI00
- K2.6 技能功能发布: https://finance.sina.com.cn/tech/roll/2026-04-21/doc-inhvfqcn6994853.shtml
- Agent 文件机制（二手引用官方文档）: https://juejin.cn/post/7670805877586132998
