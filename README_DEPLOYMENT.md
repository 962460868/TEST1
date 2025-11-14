# Gradio 版本部署说明

## 腾讯云宝塔面板部署指南

### 服务器信息
- 公网IP: 43.154.84.14
- 应用端口: 7860

### 部署步骤

#### 1. 准备环境

在宝塔面板中安装：
- Python 3.8 或更高版本
- Python 包管理器 pip

#### 2. 上传代码

将以下文件上传到服务器：
- `app_gradio.py` - 主应用文件
- `requirements.txt` - 依赖列表
- `start.sh` - 启动脚本

#### 3. 安装依赖

在服务器上执行：
```bash
cd /path/to/your/project
pip install -r requirements.txt
```

#### 4. 启动应用

##### 方法一：直接运行
```bash
python app_gradio.py
```

##### 方法二：使用启动脚本
```bash
chmod +x start.sh
./start.sh
```

##### 方法三：使用 nohup 后台运行
```bash
nohup python app_gradio.py > app.log 2>&1 &
```

##### 方法四：使用 systemd（推荐生产环境）

创建服务文件 `/etc/systemd/system/gradio-app.service`：
```ini
[Unit]
Description=Gradio AI Image Processing Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python app_gradio.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
systemctl daemon-reload
systemctl start gradio-app
systemctl enable gradio-app
systemctl status gradio-app
```

#### 5. 配置防火墙

在宝塔面板安全组中开放端口 7860：
1. 进入宝塔面板 → 安全
2. 添加规则：端口 7860，允许所有IP访问

在腾讯云控制台配置安全组：
1. 登录腾讯云控制台
2. 找到对应的云服务器实例
3. 配置安全组规则：开放 TCP 7860 端口

#### 6. 访问应用

通过浏览器访问：
```
http://43.154.84.14:7860
```

### 功能说明

应用包含以下功能：
1. **去水印** - 智能去除图片中的水印
2. **溶图打光** - 智能溶图打光处理
3. **姿态迁移** - 角色图片姿态迁移
4. **图像优化** - 支持 WAN 2.1 和 WAN 2.2 模型

### 注意事项

1. **端口配置**：默认使用 7860 端口，可在 `app_gradio.py` 中修改
2. **性能优化**：如需处理大量并发请求，建议配置 Nginx 反向代理
3. **日志管理**：生产环境建议配置日志轮转
4. **进程管理**：建议使用 systemd 或 supervisor 管理进程

### 使用 Nginx 反向代理（可选）

在宝塔面板中配置网站，添加反向代理：

```nginx
location / {
    proxy_pass http://127.0.0.1:7860;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket 支持
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # 超时设置
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
}
```

### 故障排查

#### 应用无法启动
- 检查 Python 版本：`python --version`
- 检查依赖是否安装：`pip list`
- 查看错误日志：`cat app.log`

#### 无法访问
- 检查端口是否开放：`netstat -tlnp | grep 7860`
- 检查防火墙规则
- 检查安全组配置

#### 处理速度慢
- 检查网络连接
- 查看 API 响应时间
- 考虑升级服务器配置

### 停止应用

使用 systemd：
```bash
systemctl stop gradio-app
```

直接运行的情况：
```bash
# 查找进程
ps aux | grep app_gradio.py
# 停止进程
kill <PID>
```

### 更新应用

1. 上传新版本文件
2. 停止当前运行的应用
3. 重新启动应用

使用 systemd：
```bash
systemctl restart gradio-app
```
