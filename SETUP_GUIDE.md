# A4S Chem-Lab 多机协作搭建手册

> 搭建日期：2026-07-17
> 版本：v1.0

---

## 一、整体架构

```
传感前锋（Linux 服务器，OpenClaw）
  │  写 task → push → review 结果
  │
GitHub 私有仓库（majosan/A4S-Chem-Lab-）
  │  任务板 + 共享文档 + 项目文件
  │
  ├── 🏢 公司台式 (WS) — WSL + Claude Code
  ├── 💻 笔记本 (LP)   — WSL + Claude Code
  └── 🏠 家里台式 (HM) — WSL + Claude Code

独立仓库：majosan/labvla-mujoco（模型权重单独存放）
```

## 二、每台机器的搭建步骤

### 前置条件
- VS Code 已安装
- Claude Code 插件已安装（Ctrl+Shift+P → Claude: Start）
- WSL（Windows Subsystem for Linux）已启用（推荐）

### Step 1: 生成 SSH Key

```bash
# 在 WSL 终端执行
ssh-keygen -t ed25519 -C "机器标识@a4s"
# 一路回车，不要设密码

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

### Step 2: 添加 GitHub Deploy Key

浏览器打开 `https://github.com/majosan/A4S-Chem-Lab-/settings/keys`

→ **Deploy keys** → **Add deploy key**

| 字段 | 值 |
|------|-----|
| Title | 机器名称（如 `WSL Desktop`） |
| Key | 粘贴上一步复制的公钥 |
| ✅ | 勾选 **Allow write access** |

### Step 3: Clone 仓库

```bash
cd ~/projects
git clone git@github.com:majosan/A4S-Chem-Lab-.git
cd A4S-Chem-Lab-
```

### Step 4: 配置 Git 用户信息

```bash
git config --global user.email "josan@a4s.chem-lab"
git config --global user.name "Josan"
```

### Step 5: 更新 bridge.ps1 的机器标识

用 VS Code 打开 `bridge.ps1`，修改第 34 行：

```powershell
$MACHINE_NAME = "WS"   # 公司台式
# 或
$MACHINE_NAME = "LP"   # 笔记本
# 或
$MACHINE_NAME = "HM"   # 家里台式
```

### Step 6: 拉取任务

```bash
git pull
```

### Step 7: 启动 Claude Code

```bash
code .
```

VS Code 打开后按 **Ctrl+Shift+P** → `Claude: Start`

告诉 Claude Code："Read tasks/xxx.md and execute it"

### Step 8: 完成后推送

```bash
git add -A
git commit -m "[WS] 完成了xxx任务"
git push
```

---

## 三、多项目管理（LabVLA 项目）

如果也管理 LabVLA 项目，需额外配置：

### 3.1 生成第二把 SSH Key

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_labvla -C "wsl@labvla"
cat ~/.ssh/id_ed25519_labvla.pub
```

### 3.2 加 Deploy Key 到 LabVLA 仓库

`https://github.com/majosan/labvla-mujoco/settings/keys` → **Deploy keys** → **Add deploy key**

| 字段 | 值 |
|------|-----|
| Title | `WSL LabVLA` |
| Key | 粘贴上面公钥 |
| ✅ | 勾选 **Allow write access** |

### 3.3 配置 SSH 自动选 Key

```bash
echo -e "\nHost github.com-labvla\n    HostName github.com\n    IdentityFile ~/.ssh/id_ed25519_labvla" >> ~/.ssh/config
```

### 3.4 设置远程仓库

```bash
cd ~/projects/labvla-mujoco
git remote add origin git@github.com-labvla:majosan/labvla-mujoco.git
```

### 3.5 使用多项目命令

```powershell
.\bridge.ps1 pull              # 拉 A4S 任务
.\bridge.ps1 go labvla         # 切到 LabVLA 项目
.\bridge.ps1 push labvla "消息" # 推送到 LabVLA 仓库
.\bridge.ps1 projects          # 查看所有项目
```

---

## 四、日常工作流程

### 每天早上

```bash
cd ~/projects/A4S-Chem-Lab-
git pull
cat tasks/*.md                  # 看看有没有新任务
```

### 接收任务执行

```bash
code .                          # 打开 VS Code
# Ctrl+Shift+P → Claude: Start
# 让 Claude Code 读并执行 task
```

### 完成任务

```bash
git add -A
git commit -m "[WS/机器标识] 任务完成描述"
git push
```

---

## 五、任务文件格式（供传感前锋参考）

每个 task 放在 `tasks/` 目录下，命名规则：

```
T<序号>-<机器代号>-<简短英文描述>.md
```

| 代号 | 机器 |
|------|------|
| WS | 公司台式 |
| LP | 笔记本 |
| HM | 家里台式 |
| ALL | 任意机器 |

task 内容模板：

```markdown
# T001-WS-TaskName

- Status: PENDING
- Assignee: Company Desktop
- Priority: HIGH
- Project: a4s

## Description

...

## Deliverables

...

## Notes

...
```

字段说明：
- `Status`: PENDING / IN_PROGRESS / COMPLETED / CANCELLED
- `Priority`: HIGH / MEDIUM / LOW
- `Project`: a4s / labvla

---

## 六、分仓策略

| 仓库 | URL | 用途 | 服务器权限 |
|------|-----|------|-----------|
| A4S-Chem-Lab- | `github.com/majosan/A4S-Chem-Lab-` | 任务中枢 + 项目文档 | write |
| labvla-mujoco | `github.com/majosan/labvla-mujoco` | LabVLA 代码 + 配置 | read-only |

> 模型权重等大文件（>50MB）不提交到 Git，在 `.gitignore` 中排除。

---

## 七、故障排查

### bridge.ps1 报编码错误

```powershell
# 确保文件是 UTF-8 with BOM 编码
# 在 VS Code 右下角点击编码 → "Save with Encoding" → UTF-8 with BOM
```

### SSH 认证失败

```bash
ssh -T git@github.com
# 应该输出: "Hi xxx! You've successfully authenticated..."

ssh -T git@github.com-labvla  
# 如果是 LabVLA 仓库
```

### git push 被拒绝

```bash
git pull --rebase    # 先拉取最新
git push             # 再推送
```

---

*本文档由传感前锋生成于 2026-07-17，随 A4S-Chem-Lab 仓库持续更新。*
