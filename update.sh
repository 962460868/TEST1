#!/bin/bash

# 图片处理应用更新脚本
# 使用方法：bash update.sh [分支名]

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}开始更新图片处理应用${NC}"
echo -e "${GREEN}========================================${NC}"

# 进入项目目录
cd /root/TEST1 || { echo -e "${RED}错误：无法进入项目目录 /root/TEST1${NC}"; exit 1; }

# 获取分支参数，默认为当前分支
BRANCH=${1:-$(git rev-parse --abbrev-ref HEAD)}

echo -e "${YELLOW}当前分支：$(git rev-parse --abbrev-ref HEAD)${NC}"
echo -e "${YELLOW}目标分支：${BRANCH}${NC}"

# 保存未提交的更改（如果有）
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}检测到未提交的更改，正在保存...${NC}"
    git stash save "Auto-stash before update $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 拉取最新代码
echo -e "${YELLOW}正在拉取最新代码...${NC}"
git fetch origin

# 切换到目标分支并更新
echo -e "${YELLOW}切换到分支 ${BRANCH}...${NC}"
git checkout ${BRANCH}

echo -e "${YELLOW}合并远程更新...${NC}"
git pull origin ${BRANCH}

# 恢复之前保存的更改（如果有）
if git stash list | grep -q "Auto-stash before update"; then
    echo -e "${YELLOW}恢复之前保存的更改...${NC}"
    git stash pop
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}提示：如果应用正在运行，请重启应用以应用更改${NC}"
echo -e "${YELLOW}重启命令示例：${NC}"
echo -e "  ${GREEN}pkill -f app_gradio.py && nohup python3 app_gradio.py > app.log 2>&1 &${NC}"
