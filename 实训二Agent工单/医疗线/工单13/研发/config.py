# -*- coding: utf-8 -*-
"""
work_order_13 影像分析 - 配置文件
工单编号：人工智能NLP-Agent数字人项目-13-影像分析
"""
import os

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# 大模型配置 (DashScope Qwen-VL 多模态)
# ============================================================
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VQA_MODEL = os.getenv("VQA_MODEL", "qwen-vl-max")
REPORT_MODEL = os.getenv("REPORT_MODEL", "qwen-plus")

# ============================================================
# 本地知识库路径 (复用 WO12 的知识图谱)
# ============================================================
KG_DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "work_order_12_健康咨询", "data", "medical_kg.db")

# ============================================================
# 服务配置
# ============================================================
HOST = "0.0.0.0"
PORT = 8013
