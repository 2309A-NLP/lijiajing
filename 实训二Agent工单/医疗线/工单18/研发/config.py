# 工单编号：人工智能NLP-Agent数字人项目-18-智能导览
"""配置文件"""

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 7878

# LLM 配置
LLM_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_API_KEY = "sk-xxx"  # 需要替换为实际API Key
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# 地图配置（模拟）
DEFAULT_LOCATION = {"lat": 39.9, "lng": 116.4}  # 北京
SEARCH_RADIUS = 5.0  # 公里
