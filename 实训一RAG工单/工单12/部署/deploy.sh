#!/bin/bash
# 工单12：LightRAG 部署脚本

echo "=== 工单12 LightRAG知识图谱系统 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装依赖（含LightRAG）..."
pip install -r requirements.txt
pip install lightrag-hku

# 2. 检查 Milvus
echo "[2/4] 检查 Milvus..."
docker ps | grep milvus || docker-compose up -d milvus

# 3. 构建知识图谱
echo "[3/4] 构建知识图谱（实体+关系抽取）..."
python -c "
from light_rag import LightRAGWrapper
rag = LightRAGWrapper()
rag.build_graph('data/')
stats = rag.get_stats()
print(f'实体数: {stats[\"entities\"]}，关系数: {stats[\"relations\"]}')
"

# 4. 启动应用
echo "[4/4] 启动LightRAG应用..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
