# -*- coding: utf-8 -*-
"""
work_order_12 健康咨询 - 配置文件
工单编号：人工智能NLP-Agent数字人项目-12-健康咨询
"""
import os

# ============================================================
# 数据库配置 (SQLite 模拟 Neo4j 图谱结构)
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "medical_kg.db")
JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "medical.json")

# ============================================================
# LLM 配置 (通过 Ollama 或 OpenAI 兼容接口)
# ============================================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://172.21.144.1:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:latest")

# ============================================================
# Agent 提示词模板
# ============================================================
SYSTEM_PROMPT = """你是一个专业的医疗健康咨询助手。
请基于以下从知识图谱中检索到的信息，回答用户的问题。
要求：
1. 回答要准确、专业、通俗易懂
2. 如果知识图谱中没有相关信息，请明确告知用户
3. 涉及用药请给出标准剂量提示
4. 回答末尾加上"建议及时就医，遵医嘱为准"的免责声明

知识图谱检索结果：
{kg_context}

用户问题：
{query}
"""

# ============================================================
# Cypher 查询模板映射 (关系类型 -> SQL 查询)
# ============================================================
RELATION_MAP = {
    "has_pathogen": {"label": "致病病原体", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_pathogen'"},
    "has_transmission_route": {"label": "传播途径", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_transmission_route'"},
    "has_symptom": {"label": "典型症状", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_symptom'"},
    "has_lab_result": {"label": "实验室检查", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_lab_result'"},
    "has_treatment": {"label": "治疗药物", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_treatment'"},
    "has_complication": {"label": "并发症", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_complication'"},
    "has_tcm_treatment": {"label": "中医治疗", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_tcm_treatment'"},
    "has_prevention": {"label": "预防措施", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_prevention'"},
    "has_nursing_point": {"label": "护理要点", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_nursing_point'"},
    "has_dietary_restriction": {"label": "饮食禁忌", "query": "SELECT n2.name, n2.properties FROM edges e JOIN nodes n1 ON e.source_id = n1.id JOIN nodes n2 ON e.target_id = n2.id WHERE n1.name = ? AND e.relation = 'has_dietary_restriction'"},
}
