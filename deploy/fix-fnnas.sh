#!/bin/bash
# 飞牛 NAS Dockerfile 修复脚本
# 解决 docker.fnnas.com 401 Unauthorized 问题

cd /vol1/1000/dockers/DjangoBlog-main

# 1. 移除 syntax 声明
sed -i '/^# syntax=docker\/dockerfile/d' deploy/Dockerfile

# 2. 移除 BuildKit 缓存挂载语法
sed -i 's/RUN --mount=type=cache,target=\/root\/\.cache\/pip \\$/RUN/' deploy/Dockerfile

echo "✅ Dockerfile 已修复，重新部署..."
bash deploy/auto-deploy.sh
