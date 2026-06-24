# -*- coding: utf-8 -*-
"""
配置模块
工单编号：人工智能NLP-Agent数字人项目-记账本任务
"""
import os

# ============================================================
# LLM 配置（使用 OpenAI 兼容接口，可切换 DashScope/FreeModel 等）
# ============================================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# ============================================================
# 数据库配置
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "money_notes.db")

# ============================================================
# 家庭成员白名单
# ============================================================
FAMILY_MEMBERS = ["爸爸", "妈妈", "女儿"]

# ============================================================
# 系统提示词
# ============================================================
SYSTEM_PROMPT = """你是一个家庭记账本助手。你的任务是从用户的自然语言中提取记账信息，或执行查询/删除操作。

【输出格式】
请始终返回 JSON，不要输出任何其他内容。JSON 结构如下：

1. 记账操作（新增支出/收入）：
{
  "action": "record",
  "member": "爸爸|妈妈|女儿",
  "date": "YYYY-MM-DD",
  "category": "类别如：购物/餐饮/交通/工资/报销等",
  "item": "具体事项描述",
  "amount": 数字（正数为收入，负数为支出）,
  "type": "支出|收入",
  "confirm_needed": false
}

2. 查询操作：
{
  "action": "query",
  "member": "成员名或null表示全部",
  "date_start": "YYYY-MM-DD或null",
  "date_end": "YYYY-MM-DD或null",
  "category": "类别或null",
  "confirm_needed": false
}

3. 删除操作：
{
  "action": "delete",
  "target": "删除目标的描述",
  "confirm_needed": true
}

4. 信息不完整需要引导：
{
  "action": "guide",
  "missing_fields": ["缺少的字段列表"],
  "guide_text": "引导用户补充的话"
}

【规则】
- 日期：如果用户说"今天""昨天""这个月"等，推断为对应日期。今天是 {today}
- 金额：支出用负数，收入用正数
- 如果信息不完整（缺少金额、人物、事项等），返回 action=guide
- 删除操作必须 confirm_needed=true，等待用户确认
- 只输出 JSON，不要 Markdown 代码块，不要其他文字
"""
