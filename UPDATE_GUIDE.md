# 🔄 应用更新指南

## 📌 重要说明

**GitHub 代码更新后，腾讯云服务器上的应用不会自动更新！**

你需要手动在服务器上执行更新操作。不过别担心，我已经为你准备好了超简单的更新方法！

---

## 🚀 方法一：一键更新（推荐）

### 使用更新脚本

我已经为你创建了自动更新脚本 `update.sh`，只需一个命令即可完成所有更新操作！

#### 1. 连接到服务器
```bash
ssh root@43.154.84.14
```

#### 2. 进入项目目录
```bash
cd /root/TEST1
```

#### 3. 执行更新脚本
```bash
bash update.sh
```

或者：
```bash
chmod +x update.sh
./update.sh
```

#### 更新脚本会自动完成以下操作：
- ✅ 停止正在运行的应用
- ✅ 备份当前代码
- ✅ 从 GitHub 拉取最新代码
- ✅ 更新 Python 依赖
- ✅ 重启应用
- ✅ 验证应用状态

#### 更新完成后的输出示例：
```
======================================
🔄 开始更新应用...
======================================

⏹️  步骤 1/5: 停止应用...
✅ 应用进程已停止

💾 步骤 2/5: 备份当前代码...
✅ 代码已备份到 backups/backup_20241114_103045/

📥 步骤 3/5: 从 GitHub 拉取最新代码...
✅ 代码更新成功

📝 最新提交信息：
36393f7 - Your Name, 2 minutes ago : 添加新功能

📦 步骤 4/5: 更新 Python 依赖...
✅ 依赖更新成功

🚀 步骤 5/5: 重启应用...
✅ 应用已启动，进程 ID: 12345

🔍 验证应用状态...
✅ 应用正在监听端口 7860

======================================
✨ 更新完成！
======================================
```

---

## 🔧 方法二：手动更新

如果你想更好地控制更新过程，可以手动执行每个步骤：

### 1. 连接服务器
```bash
ssh root@43.154.84.14
```

### 2. 进入项目目录
```bash
cd /root/TEST1
```

### 3. 停止应用

#### 如果使用 systemd 服务
```bash
systemctl stop gradio-app
```

#### 如果使用后台进程
```bash
pkill -f app_gradio.py
```

### 4. 拉取最新代码
```bash
# 拉取最新代码
git pull origin claude/gradio-version-deployment-017o5CUzu7UF7MTtUkgwbrY2

# 查看最新提交
git log -1
```

### 5. 更新依赖（如果 requirements.txt 有变化）
```bash
pip3 install -r requirements.txt --upgrade
```

### 6. 重启应用

#### 如果使用 systemd 服务
```bash
systemctl start gradio-app
systemctl status gradio-app
```

#### 如果使用后台进程
```bash
nohup python3 app_gradio.py > app.log 2>&1 &
```

### 7. 验证应用
```bash
# 查看进程
ps aux | grep app_gradio

# 查看端口
netstat -tlnp | grep 7860

# 查看日志
tail -f app.log
```

---

## 🤖 方法三：自动化部署（高级）

如果你希望 GitHub 代码更新后自动部署，可以使用 **GitHub Webhooks + 自动部署脚本**。

### 优点
- ✅ GitHub 推送代码后自动部署
- ✅ 无需手动登录服务器
- ✅ 提高开发效率

### 缺点
- ⚠️ 配置稍微复杂
- ⚠️ 需要额外的安全配置
- ⚠️ 需要服务器运行 webhook 监听服务

### 自动化部署架构
```
GitHub 代码推送
    ↓
触发 Webhook
    ↓
服务器接收 Webhook 请求
    ↓
执行更新脚本
    ↓
应用自动更新
```

### 实现步骤（可选）

#### 1. 安装 webhook 工具
```bash
# 安装 webhook（Go 语言实现）
wget https://github.com/adnanh/webhook/releases/download/2.8.0/webhook-linux-amd64.tar.gz
tar -xvf webhook-linux-amd64.tar.gz
mv webhook-linux-amd64/webhook /usr/local/bin/
chmod +x /usr/local/bin/webhook
```

#### 2. 创建 webhook 配置文件
```bash
nano /root/TEST1/webhook.json
```

内容：
```json
[
  {
    "id": "update-gradio-app",
    "execute-command": "/root/TEST1/update.sh",
    "command-working-directory": "/root/TEST1",
    "response-message": "应用正在更新...",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha1",
        "secret": "your-secret-key-here",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
```

#### 3. 启动 webhook 服务
```bash
nohup webhook -hooks /root/TEST1/webhook.json -verbose -port 9000 > webhook.log 2>&1 &
```

#### 4. 开放 webhook 端口
```bash
# 防火墙
firewall-cmd --permanent --add-port=9000/tcp
firewall-cmd --reload

# 腾讯云安全组也需要开放 9000 端口
```

#### 5. 配置 GitHub Webhook
1. 进入你的 GitHub 仓库
2. Settings → Webhooks → Add webhook
3. **Payload URL**: `http://43.154.84.14:9000/hooks/update-gradio-app`
4. **Content type**: `application/json`
5. **Secret**: 填写你在 webhook.json 中设置的密钥
6. **触发事件**: 选择 "Just the push event"
7. 保存

#### 6. 测试自动部署
1. 在本地修改代码
2. 提交并推送到 GitHub
3. GitHub 会自动触发 webhook
4. 服务器收到通知后自动执行更新

---

## 📋 更新检查清单

在每次更新前，建议检查：

- [ ] 确认要更新的分支是否正确
- [ ] 查看 GitHub 上的最新提交内容
- [ ] 确认是否有破坏性更改
- [ ] 备份重要数据（更新脚本会自动备份）
- [ ] 选择低流量时段更新（如果有用户在使用）

---

## 🔍 更新后验证

### 1. 检查应用是否运行
```bash
ps aux | grep app_gradio
```

### 2. 检查端口监听
```bash
netstat -tlnp | grep 7860
# 或
ss -tlnp | grep 7860
```

### 3. 查看日志
```bash
tail -f app.log
```

### 4. 测试访问
在浏览器打开：`http://43.154.84.14:7860`

### 5. 测试功能
- 上传测试图片
- 测试各个功能（去水印、溶图打光等）
- 确认处理正常

---

## 🚨 回滚到上一版本

如果更新后出现问题，可以快速回滚：

### 方法 1: 使用备份
```bash
cd /root/TEST1

# 查看备份
ls -la backups/

# 停止应用
pkill -f app_gradio.py

# 恢复备份（替换为实际备份目录名）
cp backups/backup_YYYYMMDD_HHMMSS/app_gradio.py ./
cp backups/backup_YYYYMMDD_HHMMSS/requirements.txt ./

# 重启应用
nohup python3 app_gradio.py > app.log 2>&1 &
```

### 方法 2: 使用 Git 回滚
```bash
cd /root/TEST1

# 停止应用
pkill -f app_gradio.py

# 查看提交历史
git log --oneline -5

# 回滚到指定提交（替换 <commit-hash> 为实际的提交哈希）
git reset --hard <commit-hash>

# 重启应用
nohup python3 app_gradio.py > app.log 2>&1 &
```

---

## 💡 最佳实践

### 1. 定期更新
- 建议每周检查一次 GitHub 是否有更新
- 使用 `git log` 查看更新内容

### 2. 测试环境
- 如果有条件，先在测试环境测试更新
- 确认无问题后再更新生产环境

### 3. 备份策略
- 更新脚本会自动备份代码
- 重要数据建议单独备份

### 4. 监控日志
- 更新后及时查看日志
- 发现异常及时处理

### 5. 用户通知
- 如果有用户在使用，更新前提前通知
- 选择低流量时段更新

---

## 📞 常见问题

### Q1: 更新脚本执行失败怎么办？
```bash
# 查看详细错误信息
bash -x update.sh

# 检查文件权限
chmod +x update.sh

# 手动执行每个步骤
```

### Q2: Git pull 提示冲突怎么办？
```bash
# 查看冲突文件
git status

# 方法 1: 放弃本地修改
git reset --hard origin/claude/gradio-version-deployment-017o5CUzu7UF7MTtUkgwbrY2

# 方法 2: 保存本地修改
git stash
git pull
git stash pop  # 如果需要恢复本地修改
```

### Q3: 更新后应用无法启动？
```bash
# 查看日志
tail -n 50 app.log

# 检查依赖
pip3 install -r requirements.txt

# 检查 Python 版本
python3 --version

# 尝试手动启动查看错误
python3 app_gradio.py
```

### Q4: 如何查看当前版本？
```bash
cd /root/TEST1
git log -1
git branch -a
```

### Q5: 更新后功能异常？
1. 查看日志：`tail -f app.log`
2. 检查 GitHub 的 Issues 和 Commits
3. 回滚到上一版本
4. 联系开发者

---

## 🎯 快速命令参考

```bash
# 一键更新
bash /root/TEST1/update.sh

# 手动更新
cd /root/TEST1 && \
pkill -f app_gradio.py && \
git pull && \
pip3 install -r requirements.txt --upgrade && \
nohup python3 app_gradio.py > app.log 2>&1 &

# 查看应用状态
ps aux | grep app_gradio
netstat -tlnp | grep 7860
tail -f /root/TEST1/app.log

# 重启应用
pkill -f app_gradio.py && \
cd /root/TEST1 && \
nohup python3 app_gradio.py > app.log 2>&1 &
```

---

## 📊 更新流程图

```
┌─────────────────────┐
│  GitHub 代码更新    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 你需要手动操作！    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SSH 连接到服务器    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 执行 update.sh      │
└──────────┬──────────┘
           │
           ├─→ 停止应用
           ├─→ 拉取代码
           ├─→ 更新依赖
           ├─→ 重启应用
           └─→ 验证状态
           │
           ▼
┌─────────────────────┐
│    更新完成！       │
└─────────────────────┘
```

---

## 🎉 总结

### 最简单的更新方式：
1. SSH 连接服务器：`ssh root@43.154.84.14`
2. 执行更新脚本：`bash /root/TEST1/update.sh`
3. 验证更新：访问 `http://43.154.84.14:7860`

就这么简单！✨

### 想要自动化？
参考上面的"方法三：自动化部署"章节，配置 GitHub Webhook。

### 遇到问题？
查看本文档的"常见问题"和"故障排查"章节。
