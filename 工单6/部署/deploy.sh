#!/bin/bash
# 工单6：混合检索 部署脚本

echo "=== 工单6 混合检索系统 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装依赖（含BM25）..."
pip install -r requirements.txt
pip install rank-bm25 jieba

# 2. 检查 Milvus
echo "[2/4] 检查 Milvus..."
docker ps | grep milvus || docker-compose up -d milvus

# 3. 构建双路索引
echo "[3/4] 构建向量索引 + BM25索引..."
python -c "
from hybrid_retriever import HybridRetriever
retriever = HybridRetriever()
retriever.build_index('data/')
print('双路索引构建完成')
"

# 4. 启动应用
echo "[4/4] 启动混合检索应用..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
