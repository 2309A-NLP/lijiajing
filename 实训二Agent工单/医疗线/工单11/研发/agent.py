# -*- coding: utf-8 -*-
# 工单编号：人工智能NLP-Agent数字人项目-医疗智能体-挂号管理
"""
Agent 核心：NL2SQL 两步架构
- 查询类（query_slot / query_appt / query_schedule）：LLM 直接生成 SELECT，无占位符
- 写操作类（book / cancel）：LLM 生成 SELECT 定位目标，程序化执行 INSERT/UPDATE
"""
import json, re, datetime
from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, NL2SQL_SYSTEM
from database import execute_query, execute_write

_client = None
def get_client():
    global _client
    if _client is None:
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


# ── Step1: NL → 结构化意图 + SELECT SQL ───────────────────────────────────────
NL2SQL_SYSTEM_V2 = """你是医院挂号系统智能助手。根据用户的自然语言，输出 JSON。

【数据库表结构】
users(user_id, name, phone)
children(child_id, user_id, name, age)
doctors(doctor_id, name, dept, title, schedule_json)   -- title: 专家/普通
slots(slot_id, doctor_id, slot_date, slot_time, total, remaining)
appointments(appt_id, user_id, child_id, slot_id, status, created_at) -- status: active/cancelled

【只输出 JSON，不要解释】
{
  "intent": "query_slot | book | cancel | query_appt | query_schedule | unknown",
  "select_sql": "一条 SELECT 语句（不含占位符?，直接用字面值）",
  "child_name": "孩子姓名或null",
  "dept": "科室名称或null",
  "title": "专家或普通或null",
  "target_date": "YYYY-MM-DD或today或null",
  "target_time": "HH:MM或null"
}

【规则】
1. select_sql 只写 SELECT，不写 INSERT/UPDATE，值直接写字面量，今天=DATE('now','localtime')，禁止使用?占位符
2. query_slot: 查可用号源（remaining>0）
3. book: 先用 select_sql 查目标 slot，child_name/dept/title/target_date/target_time 填实际值
4. cancel: select_sql 查用户的 active 预约，精确到科室/日期
5. query_schedule: 查医生 schedule_json 字段
6. 查历史预约（query_appt）：select_sql 查 appointments JOIN slots JOIN doctors
"""

def nl2intent(user_input: str, user_id: int = 1) -> dict:
    today = datetime.date.today().isoformat()
    resp = get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": NL2SQL_SYSTEM_V2},
            {"role": "user",   "content": f"{user_input}（当前用户 user_id={user_id}，今天={today}）"},
        ],
        temperature=0.01, max_tokens=600,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"intent": "unknown", "select_sql": "", "child_name": None}


# ── Step2: 根据意图执行操作 ────────────────────────────────────────────────────

def do_query(select_sql: str) -> tuple:
    """执行 SELECT，返回 (rows, error)"""
    if not select_sql:
        return [], None
    # LLM 偶尔生成 remaining>? 等带占位符的SQL，替换为字面0避免binding错误
    select_sql = re.sub(r"remaining\s*>\s*\?", "remaining > 0", select_sql)
    select_sql = re.sub(r"remaining\s*>=\s*\?", "remaining >= 1", select_sql)
    return execute_query(select_sql)


def do_book(intent_info: dict, user_id: int) -> tuple:
    """
    挂号：
    1. 用 select_sql 查 slot_id
    2. 用 child_name 查 child_id
    3. INSERT appointments + UPDATE slots remaining-1
    """
    select_sql = intent_info.get("select_sql", "")
    if not select_sql:
        return None, "无法确定号源，请提供科室、日期和时间"

    # Step A: 找号源
    slots, err = execute_query(select_sql)
    if err:
        return None, f"查询号源失败: {err}"
    if not slots:
        return None, "未找到符合条件的号源，该时间段可能已满或不存在"
    slot = slots[0]
    slot_id = slot.get("slot_id")
    if not slot_id:
        return None, "号源数据异常"

    # Step B: 找孩子（可选）
    child_id = None
    child_name = intent_info.get("child_name")
    if child_name:
        rows, _ = execute_query(
            "SELECT child_id FROM children WHERE user_id=? AND name=?",
            [user_id, child_name]
        )
        if rows:
            child_id = rows[0]["child_id"]

    # Step C: 写入预约 + 减号源
    insert_sql = (
        "INSERT INTO appointments(user_id, child_id, slot_id, status) VALUES(?,?,?,'active')"
    )
    _, err = execute_write(insert_sql, [user_id, child_id, slot_id])
    if err:
        return None, f"挂号写入失败: {err}"

    _, err2 = execute_write(
        "UPDATE slots SET remaining=remaining-1 WHERE slot_id=? AND remaining>0",
        [slot_id]
    )
    if err2:
        return None, f"号源更新失败: {err2}"

    # 返回挂号结果详情
    detail, _ = execute_query(
        """SELECT d.name as doctor, d.dept, d.title, s.slot_date, s.slot_time
           FROM slots s JOIN doctors d ON s.doctor_id=d.doctor_id WHERE s.slot_id=?""",
        [slot_id]
    )
    return detail or [{"slot_id": slot_id, "status": "挂号成功"}], None


def do_cancel(intent_info: dict, user_id: int) -> tuple:
    """
    取消：
    1. 用 select_sql 查 active 预约
    2. UPDATE status='cancelled'
    """
    select_sql = intent_info.get("select_sql", "")
    if not select_sql:
        return None, "无法确定要取消的预约"

    rows, err = execute_query(select_sql)
    if err:
        return None, f"查询预约失败: {err}"
    if not rows:
        return None, "未找到符合条件的有效预约"

    appt_id = rows[0].get("appt_id")
    if not appt_id:
        return None, "预约数据异常"

    _, err = execute_write(
        "UPDATE appointments SET status='cancelled' WHERE appt_id=? AND user_id=?",
        [appt_id, user_id]
    )
    if err:
        return None, f"取消失败: {err}"
    return rows, None


# ── Step3: 生成自然语言回复 ───────────────────────────────────────────────────
def generate_reply(user_input: str, intent: str, rows, error: str) -> str:
    if intent == "unknown":
        return "抱歉没理解您的请求，请说明科室、时间，例如：「帮我查牙科明天的号」"
    if error:
        return f"操作遇到问题：{error}"

    result_text = json.dumps(rows or [], ensure_ascii=False)[:800]
    resp = get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是医院智能挂号助手，根据数据库结果给用户简洁友好的中文回复。"},
            {"role": "user",   "content": f"用户问题：{user_input}\n意图：{intent}\n数据库结果：{result_text}"},
        ],
        temperature=0.3, max_tokens=400,
    )
    return resp.choices[0].message.content.strip()


# ── 主入口 ────────────────────────────────────────────────────────────────────
def process(user_input: str, user_id: int = 1) -> dict:
    info = nl2intent(user_input, user_id)
    intent = info.get("intent", "unknown")
    rows, error = None, None

    if intent == "book":
        rows, error = do_book(info, user_id)
    elif intent == "cancel":
        rows, error = do_cancel(info, user_id)
    elif intent in ("query_slot", "query_appt", "query_schedule"):
        rows, error = do_query(info.get("select_sql", ""))
    # unknown: rows=None, error=None → generate_reply 处理

    reply = generate_reply(user_input, intent, rows, error)
    return {
        "intent": intent,
        "sql":    info.get("select_sql"),
        "rows":   rows,
        "reply":  reply,
    }
