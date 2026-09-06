# Marvis 适配说明

## 平台信息

- **官方名称**: Marvis（马维斯）
- **开发者**: 腾讯应用宝团队
- **官方网站**: https://marvis.qq.com/
- **产品形态**: 桌面 App（Windows / macOS）+ 移动端（iOS / Android），支持手机远程操控电脑
- **一句话定位**: 操作系统层级的个人 AI 助手，主打系统级文件管理、跨端设备控制与本地隐私计算

## ⚠️ 同名产品澄清

搜索发现"Marvis"存在多个同名产品:

| 候选产品 | 开发者 | 定位 | AI Agent |
|---------|--------|------|---------|
| **Marvis（马维斯）** | 腾讯应用宝团队 | 操作系统级 AI 助手 | ✅ 是 |
| Marvis Pro | Aditya Rajveer | Apple Music 第三方播放器 | ❌ 否 |
| Marvis AI Assistant | Juniper/HPE | 企业网络运维对话助手 | ⚠️ 限网络运维 |
| MarvisX Enterprise | justaskmarvis.com | 企业自托管 AI 平台 | ⚠️ 欧洲产品 |

本文档以**腾讯 Marvis**为目标。如果你指的是 Marvis Pro 音乐播放器，则与 AI Agent 完全无关，photo-toolbox 不适用。

## 技能扩展机制

**支持**第三方技能扩展，格式与 Claude Skill 同源兼容。

### 技能目录

- **用户全局**: `~/.marvis/skills/<skill-name>/`
- 手动放置即可，**无需重启**

### SKILL.md 格式

- YAML frontmatter 字段:
  - `name`（必需，小写连字符）
  - `description`（必需，描述功能与触发场景）
  - 可选: `allowed-tools`、`disable` 等
- 与 Claude Code / Codex 格式兼容

### 触发方式

- 对话中自然语言自动匹配触发
- 也可 `@技能名称` 显式调用

### 脚本调用

支持 Python、Shell（PowerShell/Bash）脚本执行，通过 `use_skill` 工具加载。

### MCP 支持

原生支持 Model Context Protocol，"我的连接"中可自定义 MCP Server。

### 技能市场

接入腾讯 SkillHub（skills.tencent.com），应用内"技能"选项卡可一键搜索安装。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本
./install.sh marvis

# 方式二: 手动复制
cp -R photo-toolbox/ ~/.marvis/skills/photo-toolbox/

# 方式三: 符号链接
ln -s /path/to/photo-toolbox ~/.marvis/skills/photo-toolbox
```

安装后无需重启，在 Marvis 对话中说"帮我处理图片"或 `@photo-toolbox` 即可触发。

## 进阶: SkillHub 发布

将 photo-toolbox 打包上传至 SkillHub（skills.tencent.com）审核上架，Marvis 用户可一键安装。

## 验证状态

- **文档级验证**: ⚠️ 技能目录路径来自第三方开发者实测文章（掘金），非官方文档直接确认
- **本机实测**: ❌ 未安装 Marvis 实测技能加载
- **格式兼容性**: ✅ SKILL.md（name+description）格式与当前 photo-toolbox 一致
- **风险提示**: Marvis 的技能机制文档不如 Codex/Claude Code 公开透明，建议安装后实测确认

## 官方来源

- 官网: https://marvis.qq.com/
- 技能目录确认（第三方开发者实测）: https://juejin.cn/post/7651185671018086435
- MCP 连接机制: https://www.pingwest.com/w/316493
- SkillHub 集成: https://developer.cloud.tencent.cn/article/2703261
