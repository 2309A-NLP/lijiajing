# -*- coding: utf-8 -*-
"""
数据库模块 - 记账本 SQLite 操作
工单编号：人工智能NLP-Agent数字人项目-记账本任务
"""
import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def get_connection():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member TEXT NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('支出', '收入')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成: money_notes 表已就绪")


def record_entry(member, date, category, item, amount, entry_type):
    """新增一条记账记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO money_notes (member, date, category, item, amount, type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (member, date, category, item, amount, entry_type))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def query_records(member=None, date_start=None, date_end=None, category=None):
    """查询记账记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if member:
        conditions.append("member = ?")
        params.append(member)
    if date_start:
        conditions.append("date >= ?")
        params.append(date_start)
    if date_end:
        conditions.append("date <= ?")
        params.append(date_end)
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    cursor.execute(f"""
        SELECT id, member, date, category, item, amount, type, created_at
        FROM money_notes
        WHERE {where_clause}
        ORDER BY date DESC, id DESC
    """, params)
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def delete_record(row_id):
    """删除指定记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM money_notes WHERE id = ?", (row_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_by_description(member, item_keyword):
    """根据成员和事项关键词删除记录（模糊匹配）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM money_notes 
        WHERE member = ? AND item LIKE ?
    """, (member, f"%{item_keyword}%"))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected


def get_stats(member=None, date_start=None, date_end=None):
    """获取统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if member:
        conditions.append("member = ?")
        params.append(member)
    if date_start:
        conditions.append("date >= ?")
        params.append(date_start)
    if date_end:
        conditions.append("date <= ?")
        params.append(date_end)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN type='支出' THEN amount ELSE 0 END) as total_expense,
            SUM(CASE WHEN type='收入' THEN amount ELSE 0 END) as total_income
        FROM money_notes
        WHERE {where_clause}
    """, params)
    
    result = dict(cursor.fetchone())
    conn.close()
    return result
