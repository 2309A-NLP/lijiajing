#!/bin/bash
# 工单13：RAG性能优化版 部署脚本

echo "=== 工单13 性能优化版RAG系统 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装依赖..."
pip install -r requirements.txt

# 2. 检查 Milvus（IVF_FLAT索引）
echo "[2/4] 启动Milvus并优化索引参数..."
docker ps | grep milvus || docker-compose up -d milvus
sleep 3
python -c "
from vector_store import optimize_index
optimize_index(index_type='IVF_FLAT', nlist=128, nprobe=16)
print('Milvus索引优化完成')
"

# 3. 性能基准测试
echo "[3/4] 运行性能基准测试..."
python performance_analyzer.py --benchmark
echo "基准测试完成，查看各阶段耗时报告"

# 4. 启动性能监控版应用
echo "[4/4] 启动应用（含性能监控）..."
python app.py

echo "=== 部署完成，访问 http://localhost:7860 ==="
echo "性能看板：各阶段耗时实时显示在界面底部"
