# -*- coding: utf-8 -*-
# 工单编号：人工智能NLP-Agent数字人项目-医疗智能体-挂号管理

import os

# ─── LLM ─────────────────────────────────────────────────────────────────────
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY  = os.environ.get("DASHSCOPE_API_KEY", "")
LLM_MODEL    = "qwen-plus"

# ─── 数据库 ───────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "hospital.db")

# ─── NL2SQL 系统提示词 ────────────────────────────────────────────────────────
NL2SQL_SYSTEM = """你是一个医院挂号系统的智能助手。根据用户的自然语言描述，判断意图并生成对应操作。

【数据库表结构】
users(user_id, name, phone)                          -- 用户信息
children(child_id, user_id, name, age)               -- 用户的孩子信息
doctors(doctor_id, name, dept, title, schedule_json) -- 医生信息，title: 专家/普通，schedule_json存坐诊时间JSON
slots(slot_id, doctor_id, slot_date, slot_time, total, remaining)  -- 号源，slot_time如'09:00','14:00'
appointments(appt_id, user_id, child_id, slot_id, status, created_at)  -- 挂号记录，status: active/cancelled

【输出格式】只输出JSON，不要任何解释：
{
  "intent": "query_slot|book|cancel|query_appt|query_schedule",
  "sql": "SELECT/INSERT/UPDATE语句",
  "params": [],
  "reply_template": "给用户的回复模板（含{占位符}）"
}

【intent说明】
- query_slot: 查询号源
- book: 挂号（需先查slot，再INSERT appointments + UPDATE slots remaining-1）
- cancel: 取消挂号（UPDATE appointments SET status='cancelled'）
- query_appt: 查询历史预约
- query_schedule: 查询医生坐诊时间

【规则】
1. 今天日期用 DATE('now','localtime') 表示
2. 下周用 date('now','localtime','+7 days') 到 date('now','localtime','+13 days')
3. 挂号时 book 操作需要两步SQL，用分号分隔
4. 不确定意图时 intent 填 "unknown"，sql 填空字符串
"""
