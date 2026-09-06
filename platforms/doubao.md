# 豆包工作适配说明

## 平台信息

- **官方名称**: 豆包工作（电脑版）
- **开发者**: 字节跳动
- **官方网站**: https://www.doubao.com/work
- **产品形态**: 桌面 App（macOS / Windows）
- **下载**: 官网下载，"仅支持电脑下载"

## 技能扩展机制

**原生支持**本地 Skills，这是 photo-toolbox **当前已适配且实测通过**的平台。

### 技能目录

- **用户自建技能**: `<环境父目录>/workspace/.user_skills/<skill-name>/`
  - macOS 示例: `/Users/<用户名>/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills/photo-toolbox/`
  - ⚠️ 父目录随 OS 和运行环境变化，**禁止写死路径**，应从已知技能路径反查
- **系统预装技能**: `.../workspace/.skills/<skill-name>/`

### 目录结构

```
photo-toolbox/
├── SKILL.md        # 必需
├── scripts/        # 可选，可执行脚本（python3 直接跑）
├── references/    # 可选，按需加载的文档
└── assets/         # 可选，输出用模板资源
```

### SKILL.md 格式（官方严格规范）

- YAML frontmatter **仅允许两个字段**:
  - `name`（必填，技能名）
  - `description`（必填，**主触发机制**——必须写清"做什么+何时用"，触发条件放这里而不是正文）
- **官方原文**: "Do not include any other fields in YAML frontmatter."
  - `version`、`allowed-tools`、`category` 等社区常见字段**不被官方认可**，不要添加
- 正文建议 <500 行

### 触发方式

**三级渐进式披露**:
1. name + description 元数据常驻上下文（约 100 词）
2. 命中后才加载 SKILL.md 正文
3. scripts/references/assets 按需读取，脚本可不入上下文直接执行

### 脚本调用

Agent 用 Bash 工具执行 `python3 <skill_dir>/scripts/xxx.py ...`，产物通过 `present_files` 交付。

## photo-toolbox 安装

```bash
# 方式一: 使用安装脚本（自动检测豆包工作目录）
./install.sh doubao

# 方式二: 手动复制（需确认你的豆包工作目录）
cp -R photo-toolbox/ "/Users/<用户名>/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills/photo-toolbox/"
```

安装后**重启豆包工作电脑版**生效。

## 特色机制（豆包独有，其他平台可能不支持）

### 首次使用引导（Onboarding）

photo-toolbox 的 SKILL.md 包含完整的首次使用引导流程:
- 检测 `user-preferences.json` 不存在时，Agent 主动发起偏好询问
- 收集 PDF 排版、Word 排版、水印、证件照四类偏好
- 保存到 `user-preferences.json`，后续按偏好执行

> ⚠️ 此机制依赖 Agent 读取 SKILL.md 正文并遵循指令。在其他平台上，只要 Agent 能读取 SKILL.md 并执行其中的指令，该机制同样有效。但其他平台可能没有 `present_files` 等豆包专属工具，交付方式需相应调整。

### user-preferences.json 偏好机制

- 模板文件: `user-preferences.json.example`
- 实际文件: `user-preferences.json`（已被 .gitignore 排除，不会提交到仓库）
- 包含 pdf / word / watermark / id_photo 四类偏好字段

## 验证状态

- **本机实测**: ✅ photo-toolbox 已在豆包工作电脑版上实际运行，4 个脚本 + 首次引导流程均已验证
- **官方规范**: ✅ frontmatter 字段规范来自豆包工作内置的官方元 Skill `skill-creator-for-work`
- **回归保障**: 本次多平台升级**不修改**根目录 SKILL.md，豆包版功能不受影响

## 其他豆包形态

| 形态 | 技能支持 | 说明 |
|------|---------|------|
| 豆包 App / 网页版 | ❌ | 无本地技能文件，只有内置能力 |
| 扣子 Coze（国内版） | ⚠️ | 云端插件范式，需注册为 HTTP API 工具，**无法直接跑本地 Python 脚本**，不推荐 |

## 官方来源

- 豆包工作官网: https://www.doubao.com/work
- 豆包专业版支持用户自建技能: http://m.toutiao.com/group/7654772706424013364/
- frontmatter/目录规范（公开实践）: https://juejin.cn/post/7631486527864832051
