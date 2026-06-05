"""
工单13 配置文件
RAG性能瓶颈识别与优化。分析5个阶段：查询处理、检索、上下文组装、LLM生成、后处理。使用cProfile/snakeviz。目标：响应<3秒。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"
LOGS_DIR = BASE_DIR / "logs"
UI_DIR = BASE_DIR / "ui"

# 附件目录
ATTACH_DIR = r"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件"

# PDF路径
PDF_PATH = r"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书1.pdf"

# 嵌入模型
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

# LLM配置
LLM_API_URL = "http://172.21.144.1:11434"  # Ollama (Windows)
LLM_MODEL = "qwen2.5:latest"

# 向量存储
VECTOR_DB_PATH = KB_DIR / "vector_store"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# 检索配置
TOP_K = 5
SIMILARITY_THRESHOLD = 0.7

# 评估问题
EVAL_QUESTIONS = []  # 无标准测试问题，参考工单PDF描述

# 创建目录
for d in [DATA_DIR, KB_DIR, LOGS_DIR, UI_DIR, VECTOR_DB_PATH]:
    d.mkdir(parents=True, exist_ok=True)
