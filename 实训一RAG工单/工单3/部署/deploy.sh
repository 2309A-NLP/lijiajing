#!/bin/bash
# 工单3：表格解析 部署脚本

echo "=== 工单3 表格解析RAG系统 部署 ==="

# 1. 安装依赖（含表格解析库）
echo "[1/4] 安装依赖（含pdfplumber/camelot）..."
pip install -r requirements.txt
pip install pdfplumber camelot-py[cv]

# 2. 检查 Milvus
echo "[2/4] 检查 Milvus..."
docker ps | grep milvus || docker-compose up -d milvus

# 3. 解析并存储（含表格）
echo "[3/4] 解析PDF文档（文本+表格）..."
python -c "
from table_extractor import extract_tables
from vector_store import store_all
tables = extract_tables('data/')
store_all(tables)
print(f'表格数据已存储')
"

# 4. 启动应用
echo "[4/4] 启动应用..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
