"""
工单07 配置文件 - CCF竞赛数据测试评估
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"
LOGS_DIR = BASE_DIR / "logs"
UI_DIR = BASE_DIR / "ui"

# PDF路径
PDF_PATH = ""  # 使用CCF竞赛数据，非标准招股说明书

# CCF数据路径
CCF_DATA_DIR = DATA_DIR / "ccf" / "ccf_competition" / "pdf"

# 嵌入模型
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

# LLM配置
LLM_API_URL = "http://172.21.144.1:11434"
LLM_MODEL = "qwen2.5:latest"

# 向量存储
VECTOR_DB_PATH = KB_DIR / "vector_store"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# 检索配置
TOP_K = 5
SIMILARITY_THRESHOLD = 0.7

# 10个CCF金融年报测试问题
EVAL_QUESTIONS = [
    {"id": 1, "question": "平安银行2019年的营业收入和净利润分别是多少？同比增长情况如何？"},
    {"id": 2, "question": "中国平安2019年的保险业务收入是多少？集团的科技业务有哪些布局？"},
    {"id": 3, "question": "招商银行2019年的不良贷款率和拨备覆盖率分别是多少？与2018年相比有何变化？"},
    {"id": 4, "question": "邮储银行2019年的个人存款余额和营业收入分别是多少？"},
    {"id": 5, "question": "中信证券2020年的主营业务收入构成如何？各业务板块的占比和收入是多少？"},
    {"id": 6, "question": "中国人寿2020年的总投资收益率和新业务价值分别是多少？"},
    {"id": 7, "question": "招商证券2021年的营业收入和净利润是多少？其资产管理业务规模如何？"},
    {"id": 8, "question": "中国太保2021年的保险业务收入是多少？寿险和财险业务的贡献分别如何？"},
    {"id": 9, "question": "国泰君安2021年的ROE和净资本分别是多少？其在证券行业中的排名如何？"},
    {"id": 10, "question": "对比分析平安银行和招商银行2019年的零售业务战略，哪家银行的零售业务收入占比更高？"},
]

# 创建目录
for d in [DATA_DIR, KB_DIR, LOGS_DIR, UI_DIR, VECTOR_DB_PATH]:
    d.mkdir(parents=True, exist_ok=True)
