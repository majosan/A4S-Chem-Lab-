# WSL2 + MuJoCo 环境搭建指南

> 适用：Windows 11 → WSL2 (Ubuntu 22.04) 安装到 E 盘
> 目标：GPU 加速仿真 / 触觉手套数据接入 / 化学实验室仿真
> 版本：v1.0 — 2026-05-24 实测通过

---

## Step 0：准备工作

### 必备条件
- **Windows 11**（或 Windows 10 21H2+）
- **NVIDIA GPU**（GTX 1060+，推荐 RTX 30/40 系列）
- **最新 NVIDIA 驱动**（从 NVIDIA 官网下载 Game Ready / Studio 驱动）
  - WSL2 的 CUDA 由 Windows 端的 NVIDIA 驱动提供，WSL2 内**不需要再装 NVIDIA 驱动**

### 检查驱动
Windows PowerShell（普通权限即可）：
```powershell
nvidia-smi
```
确认 CUDA Version ≥ 11.8（MuJoCo MJX 需要）。

---

## Step 1：启用 WSL2

**全程使用管理员 PowerShell。** 按顺序执行，需要多次重启。

### 1a. 启用 WSL + VM 功能
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 第一次重启
Restart-Computer
```

### 1b. 安装 WSL 组件 + Ubuntu
重启后，管理员 PowerShell：
```powershell
# 设置 WSL2 为默认版本
wsl --set-default-version 2

# 安装 WSL 系统组件
wsl --install
```
完成后会提示**需要再次重启**。照做。
```powershell
# 第二次重启
Restart-Computer
```

### 1c. 安装 Ubuntu 发行版
重启后，管理员 PowerShell：
```powershell
wsl --install -d Ubuntu-22.04
```
这时会下载并安装 Ubuntu。安装完成后会自动弹出 Ubuntu 终端窗口，提示：
```
Installing, this may take a few minutes...
Create a default Unix user account:
```
在此输入你的用户名（如 `josan`），按提示设密码。设完后直接 `exit` 关掉窗口。

### 1d. 导出到 E 盘（避免占用 C 盘）
```powershell
# 确认已安装
wsl -l -v
# 应显示 Ubuntu-22.04，VERSION 为 2

# 导出到 E 盘
mkdir E:\wsl -Force
wsl --export Ubuntu-22.04 E:\wsl\ubuntu_backup.tar
wsl --unregister Ubuntu-22.04
wsl --import Ubuntu-22.04 E:\wsl\ubuntu\ E:\wsl\ubuntu_backup.tar --version 2
Remove-Item E:\wsl\ubuntu_backup.tar

# 再次确认
wsl -l -v
```

### 1e. 设置默认用户
导回到 E 盘后，默认用户会变成 root。需要手动修正：
```powershell
# 以 root 进入
wsl -d Ubuntu-22.04
```
Ubuntu 内执行：
```bash
# 如果之前已创建用户，先确认
cat /etc/passwd | grep josan
# 如果不存在，重新创建
sudo adduser josan
sudo usermod -aG sudo josan

# 设置 josan 为默认用户
echo -e "[user]\ndefault=josan" | sudo tee -a /etc/wsl.conf

# 退出
exit
```
回到 PowerShell：
```powershell
# 重启 WSL 使配置生效
wsl --terminate Ubuntu-22.04

# 重新进入，现在应以 josan 登录
wsl -d Ubuntu-22.04
```
看到 `josan@` 开头的提示符即成功。

### 磁盘布局
```
E:\wsl\
    └── ubuntu\
         ├── ext4.vhdx       ← 整个 Ubuntu 系统（按需增长）
         └── ...
```
C 盘不受影响。

---

## Step 2：WSL2 基础配置

进入 WSL2 后（`wsl` 或 `wsl -d Ubuntu-22.04`）：
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget unzip
```

---

## Step 3：安装 Python 3.11（稳定版）

⚠️ 不要用 apt 自带的 3.11（可能为 RC 版）。用 deadsnakes PPA 装稳定版。

```bash
# 加 deadsnakes 源
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装 Python 3.11 稳定版
sudo apt install -y python3.11 python3.11-dev python3.11-venv

# 设置 3.11 为默认 python3（若不执行，python3 仍是 3.10）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
sudo update-alternatives --auto python3

# 验证
python3 --version
# 应显示 Python 3.11.x（如 3.11.15）
```

> ⚠️ **如果之前误装了 3.11 RC 版本**，会导致包冲突。修复方法：
> ```bash
> sudo dpkg --remove --force-depends libpython3.11-minimal libpython3.11-stdlib
> sudo dpkg --remove --force-depends python3.11 python3.11-venv python3.11-dev
> sudo dpkg --remove --force-depends libpython3.11 libpython3.11-dev
> sudo apt --fix-broken install -y
> sudo apt update
> sudo apt install -y python3.11 python3.11-dev python3.11-venv
> ```

---

## Step 4：安装 CUDA Toolkit

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-6

# 环境变量
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证
nvcc --version
# 应显示 release 12.6, V12.6.85
```

---

## ⚠️ 重要：python3 版本管理（避免系统工具报错）

系统工具（apt 等）依赖 Python 3.10，**不要**把 `python3` 指向 3.11。

**正确做法：** 系统用 3.10，虚拟环境用 3.11。

```bash
# 确保 python3 是 3.10（给系统用）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
sudo update-alternatives --set python3 /usr/bin/python3.10
python3 --version
# 显示 Python 3.10.x

# 验证 apt 正常
sudo apt update
# 不应报 apt_pkg 错误
```

> 如果之前已经改乱了，导致 `sudo apt update` 报 `ModuleNotFoundError: No module named 'apt_pkg'`：
> ```bash
> sudo apt install --reinstall command-not-found python3-apt
> ```

---

## Step 5：创建 Python 虚拟环境 + 安装包

⚠️ 用 `python3.11`（不是 `python3`）创建虚拟环境。

```bash
# 确保 python3.11-venv 已装
sudo apt install -y python3.11-venv

# 用 python3.11 创建虚拟环境
python3.11 -m venv ~/venv/chem-lab
source ~/venv/chem-lab/bin/activate

# 自动激活（之后每次进 WSL 自动进入虚拟环境）
echo 'source ~/venv/chem-lab/bin/activate' >> ~/.bashrc

# 升级 pip
pip install --upgrade pip

# 安装 MuJoCo + JAX
pip install mujoco
pip install jax jaxlib

# 安装 PyTorch（CUDA 12.6 需指定 index-url）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# 安装其他工具
pip install numpy matplotlib gymnasium pyserial

# 全部验证
python3 -c "import mujoco; print(f'MuJoCo {mujoco.__version__} ✅')"
python3 -c "import jax; print(f'JAX 设备: {jax.devices()}')"
python3 -c "import torch; print(f'CUDA 可用: {torch.cuda.is_available()}')"
```
三个验证均通过即全部安装成功。

---

## Step 6：安装 Claude Code

Claude Code 是 AI 编码助手，直接在 WSL2 终端里使用。

```bash
# 安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
# 应显示 v20.x

# 全局安装 Claude Code
sudo npm install -g @anthropic-ai/claude-code
claude --version
# 应显示 v2.x

# 配置 API 中转（根据实际情况修改 key 和地址）
echo 'export ANTHROPIC_AUTH_TOKEN="你的API密钥"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="你的中转地址"' >> ~/.bashrc
source ~/.bashrc

# 验证
claude
# 首次启动会显示欢迎信息
```

### 使用方式
在项目目录里直接输入 `claude` 启动。可以和 Python 虚拟环境共存：
- `claude` 命令全局可用（Node.js）
- `python3` → 虚拟环境里的 3.11（已自动激活）
- 互不干扰

---

## Step 7：USB 串口转发（触觉手套用）

Windows PowerShell（管理员）：
```powershell
winget install dorssel.usbipd-win
```

插上手套后，识别设备并绑定：
```powershell
usbipd list
# 找到串口设备 BUSID，如 2-3
usbipd bind --busid 2-3 --wsl
```

WSL2 里验证：
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```
每次重插后需重新 bind。

---

## Step 8：VS Code 集成

1. Windows 端安装 VS Code
2. 安装插件：**Remote — WSL**（微软官方）
3. 在 WSL2 里执行：
```bash
code .
```
自动拉起 VS Code 并连接到 WSL2 环境。左下角显示 `WSL: Ubuntu-22.04`。

---

## 验证清单

- [ ] `wsl -l -v` → Ubuntu-22.04, VERSION 2
- [ ] `nvidia-smi`（WSL2 内）→ 能看到 GPU
- [ ] `nvcc --version` → CUDA 12.6
- [ ] `python3 --version` → 3.11.x
- [ ] `python3 -c "import mujoco"` → 无报错
- [ ] `python3 -c "import jax; print(jax.devices())"` → GPU 设备
- [ ] `python3 -c "import torch; print(torch.cuda.is_available())"` → True
- [ ] `claude --version` → 正常输出版本号
- [ ] `ls /dev/ttyUSB*`（接手套后）→ 串口设备

---

## 日常使用

| 操作 | 命令 |
|------|------|
| 进入 WSL | `wsl` 或 `wsl -d Ubuntu-22.04` |
| 退出 WSL | `exit` |
| 查看文件 | 文件管理器地址栏输 `\\wsl$\Ubuntu-22.04\home\josan` |
| 重启 WSL | `wsl --terminate Ubuntu-22.04` |
| VS Code 打开项目 | 在 WSL 里到项目目录执行 `code .` |
