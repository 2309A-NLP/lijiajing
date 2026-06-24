# -*- coding: utf-8 -*-
"""
配置模块
工单编号：人工智能NLP-Agent数字人项目-文生图智能体任务
"""
import os

# ============================================================
# LLM 配置
# ============================================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# ============================================================
# 图像生成 API 配置
# 支持多种后端：siliconflow / openai / stable_diffusion_local
# ============================================================
IMAGE_API_TYPE = os.getenv("IMAGE_API_TYPE", "siliconflow")
IMAGE_API_BASE_URL = os.getenv("IMAGE_API_BASE_URL", "https://api.siliconflow.cn/v1")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", LLM_API_KEY)
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

# ============================================================
# 输出目录
# ============================================================
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# ============================================================
# 系统提示词 - 提示词优化专家
# ============================================================
IMAGE_PROMPT_SYSTEM = """你是一个图像生成提示词优化专家。用户会给你描述一张面部图像或一个生成需求。

你的任务是：
1. 分析用户描述的面部特征
2. 为以下4个视角分别生成详细的英文图像生成提示词：
   - 正面（straight）
   - 左转30度（turn left 30 degrees）
   - 右转30度（turn right 30 degrees）
   - 扩图版本（outpainting，扩展背景环境）

【输出格式】
请始终返回 JSON，不要输出任何其他内容：
{
  "facial_features": "面部特征描述（中英文）",
  "prompts": {
    "straight": "正面视角提示词",
    "turn_left": "左转视角提示词",
    "turn_right": "右转视角提示词",
    "outpainting": "扩图视角提示词"
  },
  "negative_prompt": "通用负面提示词"
}

【提示词要求】
- 使用英文
- 包含：人物描述、面部特征、发型、眼睛、肤色、光照、背景、画质标签
- 画质标签：masterpiece, best quality, ultra detailed, photorealistic
- 保持面部特征一致性（相同的五官描述出现在所有提示词中）
"""

# ============================================================
# 系统提示词 - 文生图交互
# ============================================================
CHAT_SYSTEM = """你是一个图像生成助手。用户会告诉你他们想要生成什么样的图片。

请分析用户的需求，提取关键信息并调用图像生成工具。
"""

# ============================================================
# 通用负面提示词
# ============================================================
DEFAULT_NEGATIVE_PROMPT = "low quality, blurry, distorted, deformed, bad anatomy, worst quality, jpeg artifacts, watermark"
