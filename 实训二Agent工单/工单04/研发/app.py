#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金数据问答智能体 - 主程序入口
工单编号：人工智能NLP-Agent数字人项目-基金问答智能体任务

功能：
- NL2SQL：自然语言转 SQL 查询
- 基金数据库查询（10张表）
- 查询结果总结回答
- 批量处理 question.jsonl 测试问题

使用方式：
    # 交互模式
    python app.py
    
    # 批量处理测试问题
    python app.py --batch data/question.jsonl

环境变量：
    LLM_BASE_URL  - LLM API 地址
    LLM_API_KEY   - LLM API Key
    FUND_DB_PATH  - 基金数据库路径
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from config import DB_PATH
from database import list_tables, get_schema_info
from agent import process_question, generate_sql


def interactive_mode():
    """交互模式"""
    print("=" * 50)
    print("📊 欢迎使用基金数据问答智能体！")
    print("=" * 50)
    print(f"数据库路径: {DB_PATH}")
    
    tables = list_tables()
    if tables:
        print(f"可用数据表 ({len(tables)} 张): {', '.join(tables)}")
    else:
        print("[WARN] 数据库未加载，请先下载基金数据")
    
    print("\n示例问题：")
    print("  • 景顺长城中短债债券C基金在20210331的季报里，前三大持仓占比的债券名称是什么?")
    print("  • 请帮我查询出20210415日，建筑材料一级行业涨幅超过5%的股票数量")
    print("输入 '退出' 结束\n")
    
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
        
        if user_input.startswith("/sql "):
            # 直接生成SQL不执行
            question = user_input[5:]
            sql = generate_sql(question)
            print(f"\n🔧 生成的SQL:\n{sql}\n")
            continue
        
        if user_input.startswith("/schema"):
            schema = get_schema_info()
            print(f"\n📋 数据库结构:\n{schema}\n")
            continue
        
        # 正常问答
        print("\n🤔 正在分析...")
        result = process_question(user_input)
        
        print(f"\n🤖 基金助手：{result['answer']}")
        if result.get("sql"):
            print(f"\n🔧 SQL:\n{result['sql']}")
        if result.get("results"):
            count = len(result["results"])
            print(f"\n📊 结果: 共 {count} 条")
            if count <= 5:
                for r in result["results"]:
                    print(f"   {r}")
            else:
                print("   (仅显示前3条)")
                for r in result["results"][:3]:
                    print(f"   {r}")
        print()


def batch_mode(questions_file: str):
    """批量处理测试问题"""
    if not os.path.exists(questions_file):
        print(f"[ERROR] 问题文件不存在: {questions_file}")
        return
    
    results = []
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = [json.loads(line) for line in f if line.strip()]
    
    print(f"[INFO] 加载了 {len(questions)} 个问题")
    print(f"[INFO] 开始处理...\n")
    
    for i, q in enumerate(questions, 1):
        question = q.get("question", "")
        qid = q.get("id", i)
        
        print(f"[{i}/{len(questions)}] Q{qid}: {question[:60]}...")
        result = process_question(question)
        
        results.append({
            "id": qid,
            "question": question,
            "sql": result.get("sql"),
            "answer": result.get("answer"),
        })
        
        print(f"     → {result['answer'][:80]}...\n")
    
    # 保存结果
    output_file = os.path.join(os.path.dirname(questions_file), "answers.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    print(f"\n[INFO] 结果已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="基金数据问答智能体")
    parser.add_argument("--batch", type=str, help="批量处理问题文件路径 (JSONL)")
    args = parser.parse_args()
    
    if args.batch:
        batch_mode(args.batch)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
