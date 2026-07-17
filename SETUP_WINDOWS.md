# 🪟 Windows 机器搭建指南

每台 Windows 电脑按以下步骤操作。

## 1. 安装 Git + 配置 SSH

```powershell
# 安装 Git（如果还没有）
winget install Git.Git

# 重启 PowerShell 后：
git --version  # 确认安装成功
```

## 2. 生成 SSH Key 并添加到 GitHub

```powershell
ssh-keygen -t ed25519 -C "your-computer-name@a4s"
# 一路回车

# 复制公钥
type $env:USERPROFILE\.ssh\id_ed25519.pub | clip
```

**到 GitHub 仓库 → Settings → Deploy keys → Add deploy key** 添加（勾选 Write access）

## 3. Clone 仓库

```powershell
cd C:\projects
git clone git@github.com:majosan/A4S-Chem-Lab-.git
cd A4S-Chem-Lab-
```

## 4. 配置 bridge.ps1

用记事本打开 `bridge.ps1`，找到这行：

```powershell
$MACHINE_NAME = "WS"
```

改成对应的机器标识：

| 机器 | 标识 | 值 |
|------|------|----|
| 公司台式 | WS | `"WS"` |
| 笔记本 | LP | `"LP"` |
| 家里台式 | HM | `"HM"` |

## 5. 日常使用

```powershell
cd C:\projects\A4S-Chem-Lab-

# 拉取最新 + 看 task
.\bridge.ps1 pull

# 执行 Claude Code 干活...

# 完成后推送结果
.\bridge.ps1 push "完成了 XXX 任务"
```
