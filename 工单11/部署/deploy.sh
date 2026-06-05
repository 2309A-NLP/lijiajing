#!/bin/bash
# 工单11：Embedding微调 部署脚本

echo "=== 工单11 Embedding微调模型 部署 ==="

# 1. 安装依赖
echo "[1/4] 安装训练依赖..."
pip install -r requirements.txt
pip install sentence-transformers accelerate

# 2. 运行微调训练
echo "[2/4] 开始微调训练..."
echo "基座模型: BAAI/bge-small-zh-v1.5"
echo "损失函数: MultipleNegativesRankingLoss"
python embedding_finetune.py --train --epochs 3 --batch_size 16
echo "微调完成，模型保存至 ./finetuned_model/"

# 3. 评估微调效果
echo "[3/4] 评估微调效果..."
python embedding_finetune.py --eval
echo "评估报告已生成"

# 4. 替换Milvus Embedding
echo "[4/4] 使用微调模型重建Milvus索引..."
python -c "
from vector_store import rebuild_with_model
rebuild_with_model('./finetuned_model/')
print('索引重建完成')
"

echo "=== 微调模型部署完成 ==="
