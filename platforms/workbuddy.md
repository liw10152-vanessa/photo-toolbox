# WorkBuddy 适配说明

## 平台信息

- **官方名称**: WorkBuddy
- **开发者**: 腾讯云 CodeBuddy 团队
- **官方网站**: https://www.workbuddy.cn/
- **开放平台**: https://open.workbuddy.cn/
- **产品形态**: 桌面 App（Windows / macOS）
- **一句话定位**: 桌面级 AI Agent 办公工作台，能直接操作电脑文件与办公软件、交付可验收结果的"AI 同事"
- **开放平台上线**: 2026 年 9 月 2 日，面向第三方开发者开放 Skill / Expert / Connector 等能力

## 技能扩展机制

**支持完整的第三方技能扩展**，是 6 个平台中开放平台生态最成熟的之一。

### 技能目录（三级优先级自动发现）

| 优先级 | 作用域 | 路径 |
|--------|--------|------|
| 1 | 项目级（跟随仓库） | `.agents/skills/photo-toolbox/` |
| 2 | 工作区级 | `skills/photo-toolbox/` |
| 3 | **用户全局（跨项目共享）** | `~/.workbuddy/skills/photo-toolbox/` |

### SKILL.md 格式

- YAML frontmatter 字段:
  - `name`（必需）
  - `description`（必需，描述触发场景）
  - 可选: `allowed-tools`、`disable`、`version`、`category`、`platforms` 等
- 每个 Skill 是一个独立文件夹

### 触发方式

- AI 运行时自动读取 SKILL.md 并在匹配场景下调用
- 也可在 Skills 菜单中手动触发

### 脚本调用

- 支持 `workflow.sh` 工作流模板
- 连接器支持 **MCP+Skill** 和 **CLI+Skill** 两种方式
- photo-toolbox 采用 CLI+Skill 方式，直接调用 Python 脚本

### MCP 支持

原生内置 MCP 协议，可连接数据库、云服务 API、网页抓取等外部工具。

### 三种创建路径

1. **图形化界面新建**: 自动生成 SKILL.md
2. **导入 YAML 模板**
3. **指令反向生成**: AI 自动识别重复操作并沉淀为 Skill

### 开放平台五大生态能力

1. **Buddy 应用**
2. **专家（Expert）**
3. **Skill（技能）**
4. **连接器（Connector）**
5. **硬件**

### 技能市场

接入腾讯 SkillHub，76 万+ Skills 生态，支持一键安装。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本（用户全局）
./install.sh workbuddy

# 方式二: 手动复制（用户全局）
cp -R photo-toolbox/ ~/.workbuddy/skills/photo-toolbox/

# 方式三: 项目级安装（跟随 git 仓库）
cp -R photo-toolbox/ /path/to/project/.agents/skills/photo-toolbox/

# 方式四: 符号链接
ln -s /path/to/photo-toolbox ~/.workbuddy/skills/photo-toolbox
```

安装后**重启 WorkBuddy** 自动识别。

## 进阶: 开放平台上架

1. 访问 https://open.workbuddy.cn/ 注册开发者账号（个人或企业认证）
2. 上传 Skill YAML 配置
3. 审核（约 7 个工作日）后进入官方技能市场
4. 连接器选择 **CLI+Skill** 方式，直接调用 photo-toolbox 的 CLI 脚本

## 验证状态

- **文档级验证**: ✅ 技能目录路径、SKILL.md 格式、三级发现路径均来自腾讯云官方开发者文档与官方开放平台页面
- **本机实测**: ❌ 未安装 WorkBuddy 实测技能加载
- **格式兼容性**: ✅ SKILL.md（name+description）格式与当前 photo-toolbox 一致
- **开放平台**: ✅ 有成熟的开发者上架流程（open.workbuddy.cn）

## 官方来源

- 官网: https://www.workbuddy.cn/
- 开放平台: https://open.workbuddy.cn/
- 技能机制详解: https://cloud.tencent.com/developer/techpedia/2610/20530
- 开放平台接入教程: http://m.163.com/dy/article/L5RTH9FI0556I7IY.html
- 系统使用教程: https://cloud.tencent.cn/developer/article/2722693
