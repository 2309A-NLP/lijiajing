#!/bin/bash
# 工单1：基于PDF文档的问答系统 部署脚本

echo "=== 工单1 RAG PDF问答系统 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装Python依赖..."
pip install -r requirements.txt

# 2. 启动 Milvus（Docker）
echo "[2/4] 启动 Milvus 向量数据库..."
docker-compose up -d milvus
sleep 5

# 3. 构建知识库
echo "[3/4] 构建向量知识库..."
python -c "from vector_store import build_index; build_index()"

# 4. 启动应用
echo "[4/4] 启动 Gradio 应用..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
