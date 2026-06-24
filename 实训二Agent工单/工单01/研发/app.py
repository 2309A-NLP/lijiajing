#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记账本智能体 - 主程序入口
工单编号：人工智能NLP-Agent数字人项目-记账本任务

功能：
- 自然语言记账（记录家庭成员收入/支出）
- 自然语言查询（按成员/日期/类别查询）
- 删除记录（需确认）
- 不完整输入引导补充

使用方式：
    python app.py

环境变量：
    LLM_BASE_URL  - LLM API 地址（默认：https://api.siliconflow.cn/v1）
    LLM_API_KEY   - LLM API Key
    LLM_MODEL     - 模型名称（默认：Qwen/Qwen2.5-72B-Instruct）
"""
import sys
import os
import json
from datetime import datetime, timedelta

# 添加当前目录到 path
sys.path.insert(0, os.path.dirname(__file__))

from config import FAMILY_MEMBERS
from database import init_db, record_entry, query_records, delete_record, delete_by_description, get_stats
from agent import parse_user_input, generate_reply, confirm_delete


def handle_record(data):
    """处理记账操作"""
    member = data.get("member")
    date = data.get("date")
    category = data.get("category")
    item = data.get("item")
    amount = data.get("amount")
    entry_type = data.get("type")
    
    # 数据校验
    if not all([member, date, category, item, amount, entry_type]):
        missing = []
        if not member: missing.append("人物（爸爸/妈妈/女儿）")
        if not date: missing.append("日期")
        if not category: missing.append("类别")
        if not item: missing.append("事项")
        if amount is None: missing.append("金额")
        return False, f"信息不完整，缺少：{'、'.join(missing)}。请补充完整后再试～"
    
    row_id = record_entry(member, date, category, item, amount, entry_type)
    return True, {"row_id": row_id}


def handle_query(data):
    """处理查询操作"""
    member = data.get("member")
    date_start = data.get("date_start")
    date_end = data.get("date_end")
    category = data.get("category")
    
    records = query_records(member=member, date_start=date_start, date_end=date_end, category=category)
    return records


def handle_delete(data, user_input=None):
    """处理删除操作"""
    target = data.get("target", "")
    
    # 如果用户确认删除
    if user_input and confirm_delete(user_input):
        # 尝试从 target 中提取关键词进行删除
        parts = target.split()
        member = None
        keyword = target
        
        for m in FAMILY_MEMBERS:
            if m in target:
                member = m
                keyword = target.replace(m, "").strip()
                break
        
        if member:
            count = delete_by_description(member, keyword)
        else:
            count = 0
        
        return {"deleted": count > 0, "count": count, "details": target}
    
    # 否则返回确认提示
    return None


def resolve_date_keywords(text):
    """将 '今天'、'昨天'、'这个月' 等转换为实际日期"""
    today = datetime.now()
    if "今天" in text or "今天" in text:
        return today.strftime("%Y-%m-%d")
    elif "昨天" in text:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    return None


def format_month_range():
    """获取本月起止日期"""
    today = datetime.now()
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    month_end = today.strftime("%Y-%m-%d")
    return month_start, month_end


def main():
    """主循环"""
    print("=" * 50)
    print("📒 欢迎使用咱们小家专属记账本！")
    print("=" * 50)
    print("请按照以下格式输入账目需求：")
    print("  • 今天女儿买了双登山鞋499元")
    print("  • 7月5日妈妈收到报销1000元")
    print("  • 这个月女儿花了多少钱？")
    print("  • 删除女儿报旅游团的费用")
    print("输入 '退出' 或 'quit' 结束\n")
    
    # 初始化数据库
    init_db()
    
    pending_delete = None  # 待确认的删除操作
    
    while True:
        try:
            user_input = input("💬 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见～ 👋")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("退出", "quit", "exit", "q"):
            print("再见～ 👋")
            break
        
        # 检查是否是确认删除
        if pending_delete and confirm_delete(user_input):
            result = handle_delete(pending_delete, user_input)
            reply = generate_reply(pending_delete, result)
            print(f"🤖 记账本：{reply}")
            pending_delete = None
            continue
        
        # 处理特殊查询："看下这个月家里花钱明细"
        processed_input = user_input
        if "这个月" in user_input or "本月" in user_input:
            month_start, month_end = format_month_range()
            # 在输入中补充日期范围，帮助LLM解析
            processed_input = f"[日期范围: {month_start} 到 {month_end}] {user_input}"
        
        # 调用 LLM 解析
        data = parse_user_input(processed_input)
        action = data.get("action", "")
        
        if action == "record":
            success, result = handle_record(data)
            if success:
                reply = generate_reply(data)
            else:
                reply = result
            print(f"🤖 记账本：{reply}")
        
        elif action == "query":
            records = handle_query(data)
            reply = generate_reply(data, records)
            print(f"🤖 记账本：{reply}")
        
        elif action == "delete":
            result = handle_delete(data)
            if result is None:
                # 需要确认
                pending_delete = data
                reply = generate_reply(data)
            else:
                reply = generate_reply(data, result)
            print(f"🤖 记账本：{reply}")
        
        elif action == "guide":
            reply = generate_reply(data)
            print(f"🤖 记账本：{reply}")
        
        else:
            reply = generate_reply(data)
            print(f"🤖 记账本：{reply}")


if __name__ == "__main__":
    main()
