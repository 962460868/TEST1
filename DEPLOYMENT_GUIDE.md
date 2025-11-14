# 🚀 腾讯云服务器完整部署教程

## 服务器信息
- **公网IP**: 43.154.84.14
- **应用端口**: 7860
- **仓库地址**: https://github.com/962460868/TEST1.git

---

## 📋 目录
1. [连接到服务器](#1-连接到服务器)
2. [安装基础环境](#2-安装基础环境)
3. [克隆代码](#3-克隆代码)
4. [安装 Python 依赖](#4-安装-python-依赖)
5. [配置防火墙](#5-配置防火墙)
6. [启动应用](#6-启动应用)
7. [设置开机自启动](#7-设置开机自启动可选)
8. [验证部署](#8-验证部署)
9. [故障排查](#9-故障排查)

---

## 1. 连接到服务器

### 方法一：使用 SSH 客户端（推荐）

#### Windows 用户
使用 PuTTY 或 Windows Terminal：
```bash
ssh root@43.154.84.14
```

#### Mac/Linux 用户
打开终端：
```bash
ssh root@43.154.84.14
```

输入密码后，成功连接到服务器。

### 方法二：使用宝塔面板（如果已安装）
1. 打开浏览器访问：`http://43.154.84.14:8888`
2. 登录宝塔面板
3. 点击左侧"终端"，进入命令行界面

---

## 2. 安装基础环境

### 2.1 更新系统（可选但推荐）
```bash
# CentOS/RHEL
yum update -y

# Ubuntu/Debian
apt update && apt upgrade -y
```

### 2.2 安装 Python 3.8+

#### 检查 Python 版本
```bash
python3 --version
```

如果显示版本号 >= 3.8，跳到步骤 2.3。

#### 如果没有 Python 或版本过低，安装：

**CentOS 7/8:**
```bash
# 安装 Python 3.9
yum install -y python39 python39-pip python39-devel

# 设置默认 Python
alternatives --set python3 /usr/bin/python3.9
```

**Ubuntu 20.04/22.04:**
```bash
# 安装 Python 3.9
apt install -y python3.9 python3.9-pip python3.9-venv

# 设置为默认
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
```

### 2.3 升级 pip
```bash
python3 -m pip install --upgrade pip
```

### 2.4 安装 Git
```bash
# CentOS/RHEL
yum install -y git

# Ubuntu/Debian
apt install -y git
```

验证安装：
```bash
git --version
```

---

## 3. 克隆代码

### 3.1 选择工作目录
```bash
# 进入 root 用户主目录
cd /root

# 或者使用其他目录（如 /opt）
# cd /opt
```

### 3.2 克隆仓库
```bash
git clone https://github.com/962460868/TEST1.git
```

### 3.3 进入项目目录
```bash
cd TEST1
```

### 3.4 切换到 Gradio 分支
```bash
git checkout claude/gradio-version-deployment-017o5CUzu7UF7MTtUkgwbrY2
```

### 3.5 查看文件
```bash
ls -la
```

应该看到以下文件：
- `app_gradio.py` - Gradio 应用主文件
- `requirements.txt` - Python 依赖列表
- `start.sh` - 启动脚本
- `README_DEPLOYMENT.md` - 部署文档

---

## 4. 安装 Python 依赖

### 4.1 安装依赖包
```bash
pip3 install -r requirements.txt
```

这将安装：
- `gradio` - Web 界面框架
- `requests` - HTTP 请求库
- `Pillow` - 图像处理库

### 4.2 验证安装
```bash
pip3 list | grep -E "gradio|requests|Pillow"
```

应该显示已安装的包和版本号。

---

## 5. 配置防火墙

### 5.1 使用宝塔面板（推荐）

如果你安装了宝塔面板：

1. **打开宝塔面板**
   - 浏览器访问：`http://43.154.84.14:8888`
   - 登录宝塔面板

2. **添加防火墙规则**
   - 点击左侧菜单 "安全"
   - 点击 "添加规则"
   - 端口：`7860`
   - 协议：`TCP`
   - 策略：`允许`
   - 备注：`Gradio应用端口`
   - 点击 "确定"

### 5.2 使用命令行配置防火墙

#### CentOS 7/8 (使用 firewalld)
```bash
# 检查防火墙状态
systemctl status firewalld

# 如果未启动，启动防火墙
systemctl start firewalld

# 开放 7860 端口
firewall-cmd --permanent --add-port=7860/tcp

# 重载防火墙
firewall-cmd --reload

# 验证端口已开放
firewall-cmd --list-ports
```

#### Ubuntu (使用 ufw)
```bash
# 检查防火墙状态
ufw status

# 如果未启用，启用防火墙
ufw enable

# 开放 7860 端口
ufw allow 7860/tcp

# 查看规则
ufw status numbered
```

### 5.3 配置腾讯云安全组（重要！）

1. **登录腾讯云控制台**
   - 访问：https://console.cloud.tencent.com/

2. **找到你的云服务器**
   - 产品 → 云服务器 → 实例列表
   - 找到 IP 为 43.154.84.14 的服务器

3. **配置安全组**
   - 点击实例名称
   - 切换到 "安全组" 标签
   - 点击 "配置规则"
   - 点击 "添加规则"

4. **添加入站规则**
   - 类型：`自定义`
   - 协议端口：`TCP:7860`
   - 来源：`0.0.0.0/0`（允许所有IP访问）
   - 策略：`允许`
   - 备注：`Gradio应用`
   - 点击 "完成"

---

## 6. 启动应用

现在你有三种方式启动应用：

### 方式一：直接运行（测试用）
```bash
cd /root/TEST1
python3 app_gradio.py
```

**优点**: 简单直接，可以看到实时日志
**缺点**: 关闭 SSH 连接后应用会停止

启动后，你会看到类似输出：
```
Running on local URL:  http://0.0.0.0:7860
```

**测试访问**: 在浏览器打开 `http://43.154.84.14:7860`

按 `Ctrl + C` 可以停止应用。

### 方式二：后台运行（推荐用于测试）
```bash
cd /root/TEST1

# 使用 nohup 后台运行
nohup python3 app_gradio.py > app.log 2>&1 &

# 查看进程
ps aux | grep app_gradio

# 查看日志
tail -f app.log
```

**查看日志**:
```bash
# 实时查看日志
tail -f app.log

# 查看最后 50 行日志
tail -n 50 app.log

# 退出日志查看：按 Ctrl + C
```

**停止应用**:
```bash
# 查找进程 ID
ps aux | grep app_gradio

# 停止进程（替换 <PID> 为实际进程号）
kill <PID>

# 或者强制停止
pkill -f app_gradio.py
```

### 方式三：使用启动脚本
```bash
cd /root/TEST1

# 给脚本执行权限
chmod +x start.sh

# 后台运行
nohup ./start.sh > app.log 2>&1 &
```

---

## 7. 设置开机自启动（可选）

### 7.1 创建 systemd 服务文件

创建服务配置文件：
```bash
nano /etc/systemd/system/gradio-app.service
```

或使用 vi 编辑器：
```bash
vi /etc/systemd/system/gradio-app.service
```

### 7.2 输入以下内容

**⚠️ 注意：请根据实际路径修改 `WorkingDirectory` 和 `ExecStart`**

```ini
[Unit]
Description=Gradio AI Image Processing Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/TEST1
ExecStart=/usr/bin/python3 /root/TEST1/app_gradio.py
Restart=always
RestartSec=10
StandardOutput=append:/root/TEST1/app.log
StandardError=append:/root/TEST1/app.log

[Install]
WantedBy=multi-user.target
```

**保存文件**:
- nano: 按 `Ctrl + X`，然后按 `Y`，再按 `Enter`
- vi: 按 `Esc`，输入 `:wq`，按 `Enter`

### 7.3 启用并启动服务

```bash
# 重新加载 systemd 配置
systemctl daemon-reload

# 启动服务
systemctl start gradio-app

# 查看服务状态
systemctl status gradio-app

# 设置开机自启动
systemctl enable gradio-app
```

### 7.4 服务管理命令

```bash
# 查看服务状态
systemctl status gradio-app

# 启动服务
systemctl start gradio-app

# 停止服务
systemctl stop gradio-app

# 重启服务
systemctl restart gradio-app

# 查看日志
journalctl -u gradio-app -f

# 禁用开机自启动
systemctl disable gradio-app
```

---

## 8. 验证部署

### 8.1 检查应用是否运行
```bash
# 检查进程
ps aux | grep app_gradio

# 检查端口监听
netstat -tlnp | grep 7860

# 或使用 ss 命令
ss -tlnp | grep 7860
```

应该看到类似输出：
```
tcp        0      0 0.0.0.0:7860            0.0.0.0:*               LISTEN      12345/python3
```

### 8.2 测试本地访问
```bash
curl http://127.0.0.1:7860
```

应该返回 HTML 内容。

### 8.3 测试公网访问

在你的电脑浏览器中打开：
```
http://43.154.84.14:7860
```

你应该看到 **RunningHub AI - 智能图片处理工具** 的界面，包含四个标签：
- 🚿 去水印
- ✨ 溶图打光
- 🤸 姿态迁移
- 🎨 图像优化

### 8.4 测试功能

1. 选择任意一个功能标签
2. 上传测试图片
3. 点击处理按钮
4. 等待处理完成
5. 查看和下载结果

---

## 9. 故障排查

### 问题 1: 无法访问应用

#### 检查应用是否运行
```bash
ps aux | grep app_gradio
```

如果没有输出，说明应用未运行，需要启动：
```bash
cd /root/TEST1
python3 app_gradio.py
```

#### 检查端口是否监听
```bash
netstat -tlnp | grep 7860
```

如果没有输出，说明应用未正常启动，查看日志：
```bash
cat app.log
```

#### 检查防火墙
```bash
# CentOS
firewall-cmd --list-ports

# Ubuntu
ufw status numbered
```

确保 7860/tcp 在列表中。

#### 检查腾讯云安全组
- 登录腾讯云控制台
- 检查安全组规则
- 确保开放了 7860 端口

### 问题 2: 依赖安装失败

#### 检查 Python 版本
```bash
python3 --version
```

需要 Python 3.8 或更高版本。

#### 检查 pip
```bash
pip3 --version
```

#### 手动安装依赖
```bash
pip3 install gradio
pip3 install requests
pip3 install Pillow
```

#### 使用国内镜像源（如果下载慢）
```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: 进程意外退出

#### 查看日志
```bash
tail -n 100 app.log
```

#### 查看系统日志
```bash
# 使用 systemd 时
journalctl -u gradio-app -n 50

# 查看系统日志
tail /var/log/messages  # CentOS
tail /var/log/syslog    # Ubuntu
```

#### 常见错误

**端口被占用**:
```bash
# 查看占用 7860 端口的进程
lsof -i :7860

# 或
netstat -tlnp | grep 7860

# 停止占用端口的进程
kill <PID>
```

**内存不足**:
```bash
# 查看内存使用
free -h

# 查看系统资源
top
```

**权限问题**:
```bash
# 检查文件权限
ls -la /root/TEST1/

# 修改权限
chmod +x /root/TEST1/app_gradio.py
```

### 问题 4: 图片处理失败

#### 检查网络连接
```bash
# 测试是否能访问 API
curl -I https://www.runninghub.cn

# 测试 DNS 解析
nslookup www.runninghub.cn
```

#### 查看应用日志
```bash
tail -f app.log
```

查找错误信息。

### 问题 5: 服务无法自启动

#### 检查服务状态
```bash
systemctl status gradio-app
```

#### 检查服务配置
```bash
cat /etc/systemd/system/gradio-app.service
```

#### 查看启动日志
```bash
journalctl -u gradio-app -b
```

---

## 🎯 快速命令参考

### 启动应用
```bash
# 方法 1: 直接运行
cd /root/TEST1 && python3 app_gradio.py

# 方法 2: 后台运行
cd /root/TEST1 && nohup python3 app_gradio.py > app.log 2>&1 &

# 方法 3: 使用 systemd
systemctl start gradio-app
```

### 停止应用
```bash
# 方法 1: 停止后台进程
pkill -f app_gradio.py

# 方法 2: 使用 systemd
systemctl stop gradio-app
```

### 重启应用
```bash
# 方法 1: 先停止再启动
pkill -f app_gradio.py
cd /root/TEST1 && nohup python3 app_gradio.py > app.log 2>&1 &

# 方法 2: 使用 systemd
systemctl restart gradio-app
```

### 查看日志
```bash
# 实时查看日志
tail -f /root/TEST1/app.log

# 查看最后 50 行
tail -n 50 /root/TEST1/app.log

# 使用 systemd 时
journalctl -u gradio-app -f
```

### 查看状态
```bash
# 检查进程
ps aux | grep app_gradio

# 检查端口
netstat -tlnp | grep 7860

# 检查服务状态（systemd）
systemctl status gradio-app
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看日志文件：`tail -f /root/TEST1/app.log`
2. 检查防火墙和安全组配置
3. 确认 Python 版本 >= 3.8
4. 确认依赖已正确安装

---

## 🎉 部署成功！

访问你的应用：**http://43.154.84.14:7860**

现在你可以使用以下功能：
- 🚿 **去水印** - 智能去除图片水印
- ✨ **溶图打光** - 智能溶图打光处理
- 🤸 **姿态迁移** - 角色姿态迁移
- 🎨 **图像优化** - WAN 2.1 & WAN 2.2 模型

享受你的 AI 图片处理工具吧！🎊
