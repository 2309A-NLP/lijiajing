#!/bin/bash
# 工单7：功能测试评估 部署脚本

echo "=== 工单7 评估系统 部署 ==="

# 1. 安装依赖
echo "[1/3] 安装评估依赖..."
pip install -r requirements.txt
pip install ragas datasets openpyxl

# 2. 运行功能测试
echo "[2/3] 运行功能测试..."
python eval_test.py --mode full --output report.json
echo "测试完成，结果保存至 report.json"

# 3. 生成Excel报告
echo "[3/3] 生成Excel评估报告..."
python -c "
import json, openpyxl
with open('report.json') as f:
    data = json.load(f)
print('评估指标：', data.get('summary', {}))
"

echo "=== 评估完成 ==="
echo "查看报告：report.json"
