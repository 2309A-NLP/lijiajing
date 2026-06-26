# -*- coding: utf-8 -*-
"""
work_order_17_智能备课 - 配置文件
"""

WEB_HOST = "0.0.0.0"
WEB_PORT = 8017

# LLM 配置（模拟模式，不实际调用API）
LLM_PROVIDER = "mock"  # mock / openai / qwen
LLM_MODEL = "mock-gpt"

# Bloom 教育目标分类
BLOOM_LEVELS = ["记忆", "理解", "应用", "分析", "评价", "创造"]
