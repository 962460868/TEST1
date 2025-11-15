# 腾讯云服务器更新指南

## 方法一：使用更新脚本（推荐）

### 1. 首次使用需要先拉取更新脚本

在你的腾讯云服务器上执行：

```bash
cd /root/TEST1
git fetch origin
git checkout claude/remove-png-download-button-01JWaUsd8fyRBHjpJPCS1swA
git pull origin claude/remove-png-download-button-01JWaUsd8fyRBHjpJPCS1swA
```

### 2. 执行更新脚本

```bash
bash /root/TEST1/update.sh
```

或者指定要更新的分支：

```bash
bash /root/TEST1/update.sh claude/remove-png-download-button-01JWaUsd8fyRBHjpJPCS1swA
```

### 3. 重启应用

更新完成后，重启应用以应用更改：

```bash
# 停止当前运行的应用
pkill -f app_gradio.py

# 启动应用
cd /root/TEST1
nohup python3 app_gradio.py > app.log 2>&1 &
```

## 方法二：手动更新

### 1. 拉取最新代码

```bash
cd /root/TEST1
git fetch origin
git checkout claude/remove-png-download-button-01JWaUsd8fyRBHjpJPCS1swA
git pull origin claude/remove-png-download-button-01JWaUsd8fyRBHjpJPCS1swA
```

### 2. 重启应用

```bash
pkill -f app_gradio.py
cd /root/TEST1
nohup python3 app_gradio.py > app.log 2>&1 &
```

## 常见问题

### Q: 提示 "error: Your local changes to the following files would be overwritten"

**A:** 说明你本地有修改，需要先保存或丢弃：

保存本地修改：
```bash
git stash save "我的本地修改"
```

或者丢弃本地修改：
```bash
git checkout -- .
```

### Q: 如何查看应用运行日志？

**A:** 查看日志文件：

```bash
tail -f /root/TEST1/app.log
```

### Q: 如何确认更新是否成功？

**A:** 检查最新的提交：

```bash
cd /root/TEST1
git log --oneline -3
```

应该能看到：
- `优化图片下载功能，移除冗余下载按钮`
- `添加自动更新脚本`

## 本次更新内容

### 主要改动：

1. ✅ 移除了"下载优化后图片(PNG)"按钮
2. ✅ 移除了"PNG文件下载"栏目
3. ✅ 下载功能已集成到优化后图片右上角的下载图标
4. ✅ 下载图标放大了1.3倍，悬停时放大1.5倍
5. ✅ 确保下载的图片为PNG格式

### 使用变化：

- 之前：需要点击单独的下载按钮来下载PNG图片
- 现在：直接点击"优化后"标签页中图片右上角的下载图标即可下载PNG格式图片

界面更加简洁直观！
