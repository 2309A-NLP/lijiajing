# -*- coding: utf-8 -*-
"""
数据库模块 - 基金数据库查询
工单编号：人工智能NLP-Agent数字人项目-基金问答智能体任务
"""
import sqlite3
import os
from config import DB_PATH, FUND_TABLES_SCHEMA


def get_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        print(f"[WARN] 数据库文件不存在: {DB_PATH}")
        print("[WARN] 请从 ModelScope 下载基金数据:")
        print("  git clone https://www.modelscope.cn/datasets/BJQW14B/bs_challenge_financial_14b_dataset.git")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"[DB] 连接错误: {e}")
        return None


def get_schema_info():
    """获取数据库实际表结构信息"""
    conn = get_connection()
    if not conn:
        return FUND_TABLES_SCHEMA
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_parts = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            col_info = ", ".join([f"{col[1]} {col[2]}" for col in columns])
            schema_parts.append(f"{table}({col_info})")
        
        conn.close()
        return "可用数据表:\n" + "\n".join(schema_parts)
    except Exception as e:
        conn.close()
        print(f"[DB] 获取schema错误: {e}")
        return FUND_TABLES_SCHEMA


def execute_sql(sql: str):
    """执行 SQL 查询，返回结果列表"""
    conn = get_connection()
    if not conn:
        return None, "数据库不可用"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        return rows, None
    except sqlite3.Error as e:
        conn.close()
        return None, str(e)


def list_tables():
    """列出数据库中的所有表"""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def sample_table(table_name, n=5):
    """采样查看表数据"""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (n,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
