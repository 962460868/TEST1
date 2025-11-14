#!/bin/bash

# 应用更新脚本
# 用于从 GitHub 拉取最新代码并重启应用

echo "======================================"
echo "🔄 开始更新应用..."
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目目录（根据实际情况修改）
PROJECT_DIR="/root/TEST1"
BRANCH="claude/gradio-version-deployment-017o5CUzu7UF7MTtUkgwbrY2"

# 进入项目目录
cd $PROJECT_DIR || {
    echo -e "${RED}❌ 错误：无法进入项目目录 $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${YELLOW}📂 当前目录：$(pwd)${NC}"

# 1. 停止正在运行的应用
echo ""
echo -e "${YELLOW}⏹️  步骤 1/5: 停止应用...${NC}"

# 检查是否使用 systemd 服务
if systemctl is-active --quiet gradio-app; then
    echo "检测到 systemd 服务，正在停止..."
    systemctl stop gradio-app
    echo -e "${GREEN}✅ systemd 服务已停止${NC}"
else
    # 使用 pkill 停止进程
    if pgrep -f "app_gradio.py" > /dev/null; then
        echo "正在停止应用进程..."
        pkill -f "app_gradio.py"
        sleep 2

        # 确认进程已停止
        if pgrep -f "app_gradio.py" > /dev/null; then
            echo -e "${RED}⚠️  进程未完全停止，强制终止...${NC}"
            pkill -9 -f "app_gradio.py"
            sleep 1
        fi
        echo -e "${GREEN}✅ 应用进程已停止${NC}"
    else
        echo -e "${YELLOW}ℹ️  应用未运行${NC}"
    fi
fi

# 2. 备份当前代码（可选）
echo ""
echo -e "${YELLOW}💾 步骤 2/5: 备份当前代码...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p backups
cp -r app_gradio.py requirements.txt backups/$BACKUP_DIR/ 2>/dev/null
echo -e "${GREEN}✅ 代码已备份到 backups/$BACKUP_DIR/${NC}"

# 3. 拉取最新代码
echo ""
echo -e "${YELLOW}📥 步骤 3/5: 从 GitHub 拉取最新代码...${NC}"

# 保存本地修改（如果有）
git stash save "Auto stash before update $(date +%Y%m%d_%H%M%S)" 2>/dev/null

# 拉取最新代码
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 代码更新成功${NC}"

    # 显示最新的提交信息
    echo ""
    echo -e "${YELLOW}📝 最新提交信息：${NC}"
    git log -1 --pretty=format:"%h - %an, %ar : %s"
    echo ""
else
    echo -e "${RED}❌ 代码更新失败${NC}"
    echo -e "${YELLOW}正在恢复备份...${NC}"
    git stash pop 2>/dev/null
    exit 1
fi

# 4. 更新依赖
echo ""
echo -e "${YELLOW}📦 步骤 4/5: 更新 Python 依赖...${NC}"
pip3 install -r requirements.txt --upgrade -q

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 依赖更新成功${NC}"
else
    echo -e "${RED}⚠️  依赖更新失败，但继续...${NC}"
fi

# 5. 重启应用
echo ""
echo -e "${YELLOW}🚀 步骤 5/5: 重启应用...${NC}"

# 检查是否使用 systemd 服务
if systemctl list-unit-files | grep -q "gradio-app.service"; then
    echo "使用 systemd 服务重启..."
    systemctl start gradio-app
    sleep 3

    if systemctl is-active --quiet gradio-app; then
        echo -e "${GREEN}✅ 应用已通过 systemd 启动${NC}"
    else
        echo -e "${RED}❌ systemd 启动失败，查看状态：${NC}"
        systemctl status gradio-app --no-pager
        exit 1
    fi
else
    # 使用 nohup 后台启动
    echo "使用 nohup 后台启动..."
    nohup python3 app_gradio.py > app.log 2>&1 &
    sleep 3

    if pgrep -f "app_gradio.py" > /dev/null; then
        PID=$(pgrep -f "app_gradio.py")
        echo -e "${GREEN}✅ 应用已启动，进程 ID: $PID${NC}"
    else
        echo -e "${RED}❌ 应用启动失败，查看日志：${NC}"
        tail -n 20 app.log
        exit 1
    fi
fi

# 6. 验证应用状态
echo ""
echo -e "${YELLOW}🔍 验证应用状态...${NC}"
sleep 2

# 检查端口是否监听
if netstat -tlnp 2>/dev/null | grep -q ":7860" || ss -tlnp 2>/dev/null | grep -q ":7860"; then
    echo -e "${GREEN}✅ 应用正在监听端口 7860${NC}"
else
    echo -e "${RED}⚠️  端口 7860 未监听，请检查日志${NC}"
fi

# 显示完成信息
echo ""
echo "======================================"
echo -e "${GREEN}✨ 更新完成！${NC}"
echo "======================================"
echo ""
echo -e "${YELLOW}📊 应用信息：${NC}"
echo "  - 访问地址: http://43.154.84.14:7860"
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 当前分支: $BRANCH"
echo ""
echo -e "${YELLOW}💡 有用的命令：${NC}"
echo "  - 查看日志: tail -f $PROJECT_DIR/app.log"
echo "  - 查看进程: ps aux | grep app_gradio"
echo "  - 查看端口: netstat -tlnp | grep 7860"
if systemctl list-unit-files | grep -q "gradio-app.service"; then
    echo "  - 查看服务状态: systemctl status gradio-app"
fi
echo ""
