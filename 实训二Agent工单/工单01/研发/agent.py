# -*- coding: utf-8 -*-
"""
Agent 核心模块 - LLM 意图识别与信息抽取
工单编号：人工智能NLP-Agent数字人项目-记账本任务
"""
import json
import re
from datetime import datetime, timedelta
from openai import OpenAI
from config import (
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL,
    SYSTEM_PROMPT, FAMILY_MEMBERS
)


def get_llm_client():
    """获取 LLM 客户端"""
    return OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )


def parse_user_input(user_input, today=None):
    """
    使用 LLM 解析用户输入，返回结构化 JSON
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = SYSTEM_PROMPT.replace("{today}", today)
    
    client = get_llm_client()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=500,
    )
    
    text = response.choices[0].message.content.strip()
    
    # 清理可能的 Markdown 代码块
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "action": "error",
            "error_text": f"解析失败，请重新描述。原始响应: {text[:100]}"
        }
    
    return result


def generate_reply(action_data, db_result=None):
    """
    根据 LLM 解析结果和数据库操作结果，生成自然语言回复
    """
    action = action_data.get("action", "")
    
    if action == "record":
        return _reply_record(action_data)
    elif action == "query":
        return _reply_query(action_data, db_result)
    elif action == "delete":
        return _reply_delete(action_data, db_result)
    elif action == "guide":
        return action_data.get("guide_text", "请补充完整信息后再试～")
    elif action == "error":
        return action_data.get("error_text", "抱歉，我没理解你的意思，请换个说法试试。")
    else:
        return "抱歉，我没理解你的意思。你可以说：'今天买三体花了50元' 或 '这个月女儿花了多少钱'"


def _reply_record(data):
    """记账成功回复"""
    member = data.get("member", "")
    date = data.get("date", "")
    item = data.get("item", "")
    amount = data.get("amount", 0)
    entry_type = data.get("type", "支出")
    
    abs_amount = abs(amount)
    if entry_type == "支出":
        return f"已记录：{date}，{member}{item}，支出 {abs_amount} 元 ✅"
    else:
        return f"已记录：{date}，{member}{item}，收入 {abs_amount} 元 ✅"


def _reply_query(data, records):
    """查询结果回复"""
    member = data.get("member")
    
    if not records:
        who = f"{member}的" if member else ""
        return f"没有找到{who}相关记账记录 📭"
    
    # 计算汇总
    total_expense = sum(abs(r["amount"]) for r in records if r["type"] == "支出")
    total_income = sum(r["amount"] for r in records if r["type"] == "收入")
    
    # 生成明细
    who = f"{member}" if member else "所有成员"
    reply = f"📊 {who}的记账明细：\n"
    
    for r in records:
        sign = "-" if r["type"] == "支出" else "+"
        reply += f"  {r['date']} | {r['member']} | {r['item']} | {sign}{abs(r['amount'])}元\n"
    
    reply += f"\n💰 汇总：共{len(records)}条记录"
    if total_expense > 0:
        reply += f"，总支出 {total_expense} 元"
    if total_income > 0:
        reply += f"，总收入 {total_income} 元"
    
    return reply


def _reply_delete(data, db_result):
    """删除操作回复"""
    if db_result and db_result.get("deleted", False):
        count = db_result.get("count", 0)
        return f"已删除 {count} 条记录 🗑️\n删除内容：{db_result.get('details', '')}"
    elif db_result and not db_result.get("deleted", True):
        return "未找到匹配的记录，请确认描述是否正确 🔍"
    else:
        # confirm_needed 阶段
        target = data.get("target", "")
        return f"⚠️ 确认删除以下记录？回复'确认'即可删除。\n目标：{target}"


def confirm_delete(user_input):
    """判断用户是否在确认删除"""
    confirm_words = ["确认", "是的", "确定", "删吧", "删掉", "好", "ok", "yes"]
    text = user_input.lower()
    return any(w in text for w in confirm_words)
