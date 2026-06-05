#!/bin/bash
# 工单2：问答系统优化版 部署脚本

echo "=== 工单2 RAG优化版 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装Python依赖..."
pip install -r requirements.txt

# 2. 检查 Milvus 状态
echo "[2/4] 检查 Milvus 状态..."
docker ps | grep milvus || docker-compose up -d milvus

# 3. 重建优化后的知识库（新分块参数）
echo "[3/4] 使用优化参数重建知识库..."
echo "chunk_size=512, overlap=50, top_k=5"
python -c "from vector_store import rebuild_index; rebuild_index(chunk_size=512, overlap=50)"

# 4. 启动优化版应用
echo "[4/4] 启动优化版应用..."
python app.py

echo "=== 优化版部署完成，访问 http://localhost:7860 ==="
