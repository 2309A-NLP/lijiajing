#!/bin/bash
# 工单4：图像解析 部署脚本

echo "=== 工单4 图文解析RAG系统 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装依赖（含视觉模型）..."
pip install -r requirements.txt

# 2. 拉取 Moondream 视觉模型
echo "[2/4] 拉取 Moondream 视觉模型..."
ollama pull moondream
echo "Moondream 就绪"

# 3. 检查 Milvus
echo "[3/4] 检查 Milvus..."
docker ps | grep milvus || docker-compose up -d milvus

# 4. 启动应用
echo "[4/4] 启动图文解析应用..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
echo "提示：首次处理图像页面较慢，请耐心等待"
