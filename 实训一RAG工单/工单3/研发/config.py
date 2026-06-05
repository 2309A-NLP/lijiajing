"""
工单03 配置文件
表格解析及检索优化。新增招股说明书2.pdf（力源信息），使用表格解析技术。验收强调id=1,2,3,4必须准确。
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
# PDF路径列表（支持多PDF）
PDF_PATHS = [
    r"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书1.pdf",
    r"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书2.pdf",
]
PDF_PATH = PDF_PATHS[0]

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
EVAL_QUESTIONS = [
    {"id": 1, "question": "武汉力源信息技术股份有限公司本次发行股数是多少，占发行后总股本的比例是多少？"},
    {"id": 2, "question": "武汉力源信息技术股份有限公司本次募集资金拟投资哪些项目？"},
    {"id": 3, "question": "与武汉力源信息技术股份有限公司存在控制关系的关联方是谁，持股比例和本公司关系是什么？"},
    {"id": 4, "question": "与武汉力源信息技术股份有限公司不存在控制关系的关联方企业有哪些？"},
    {"id": 260, "question": "报告期内，武汉兴图新科电子股份有限公司来自军用领域的收入分别是多少？"},
    {"id": 95, "question": "武汉兴图新科电子股份有限公司参与制定了哪个技术标准？"},
    {"id": 33, "question": "报告期内，武汉兴图新科电子股份有限公司来自军用领域的收入占主营业务收入的比重分别是多少？"},
    {"id": 34, "question": "根据武汉兴图新科电子股份有限公司招股意向书，电子信息行业的上游涉及哪些企业？"},
    {"id": 957, "question": "武汉兴图新科电子股份有限公司在哪个领域已经成为重要供应商？"},
    {"id": 793, "question": "根据武汉兴图新科电子股份有限公司招股意向书，电子信息行业的下游主要包括哪些行业？"},
    {"id": 795, "question": "武汉兴图新科电子股份有限公司参与的哪个工程荣获了国家科技进步一等奖？"},
    {"id": 543, "question": "武汉兴图新科电子股份有限公司注册资本是多少？"},
    {"id": 531, "question": "武汉兴图新科电子股份有限公司法定代表人是谁？"},
    {"id": 207, "question": "武汉兴图新科电子股份有限公司计划使用本次发行募集资金的多少用于补充流动资金？"},
]

# 创建目录
for d in [DATA_DIR, KB_DIR, LOGS_DIR, UI_DIR, VECTOR_DB_PATH]:
    d.mkdir(parents=True, exist_ok=True)
