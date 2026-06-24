# -*- coding: utf-8 -*-
"""
Agent 核心模块 - NL2SQL + 结果总结
工单编号：人工智能NLP-Agent数字人项目-基金问答智能体任务
"""
import json
import re
from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, NL2SQL_SYSTEM, SUMMARIZE_SYSTEM
from database import get_schema_info, execute_sql


def get_llm_client():
    """获取 LLM 客户端"""
    return OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )


def generate_sql(question: str, schema: str = None) -> str:
    """
    将自然语言问题转换为 SQL 查询
    
    Args:
        question: 用户的自然语言问题
        schema: 数据库表结构信息
    Returns:
        SQL 查询语句
    """
    if schema is None:
        schema = get_schema_info()
    
    system_prompt = NL2SQL_SYSTEM.replace("{schema}", schema)
    
    client = get_llm_client()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.01,
        max_tokens=500,
    )
    
    sql = response.choices[0].message.content.strip()
    
    # 清理 Markdown 代码块
    sql = re.sub(r'^```sql\s*', '', sql)
    sql = re.sub(r'^```\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    sql = sql.strip()
    
    return sql


def summarize_answer(question: str, sql: str, results: list, error: str = None) -> str:
    """
    根据查询结果生成回答
    
    Args:
        question: 原始问题
        sql: 执行的SQL
        results: 查询结果
        error: 执行错误信息
    Returns:
        回答文本
    """
    if error:
        if "数据库不可用" in error:
            return "数据库尚未配置，请先下载基金数据并配置 DB_PATH。"
        return f"查询执行失败: {error}"
    
    if not results:
        return "未查询到相关数据。"
    
    client = get_llm_client()
    
    # 构建结果上下文
    result_text = json.dumps(results[:20], ensure_ascii=False, indent=2)  # 最多20条
    if len(results) > 20:
        result_text += f"\n... 还有 {len(results) - 20} 条结果未显示"
    
    messages = [
        {"role": "system", "content": SUMMARIZE_SYSTEM},
        {"role": "user", "content": f"问题: {question}\nSQL: {sql}\n查询结果:\n{result_text}"},
    ]
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # 降级方案：直接返回结果
        return f"查询结果（共{len(results)}条）:\n{result_text[:500]}"


def process_question(question: str) -> dict:
    """
    完整处理一个问题：NL2SQL → 执行 → 总结
    
    Args:
        question: 用户问题
    Returns:
        dict 包含 question, sql, results, answer
    """
    # Step 1: 生成 SQL
    sql = generate_sql(question)
    
    if "CANNOT_DETERMINE" in sql:
        return {
            "question": question,
            "sql": None,
            "results": None,
            "answer": "抱歉，我无法理解你的问题，请换个说法试试。"
        }
    
    # Step 2: 执行 SQL
    results, error = execute_sql(sql)
    
    # Step 3: 生成回答
    answer = summarize_answer(question, sql, results, error)
    
    return {
        "question": question,
        "sql": sql,
        "results": results,
        "answer": answer
    }
