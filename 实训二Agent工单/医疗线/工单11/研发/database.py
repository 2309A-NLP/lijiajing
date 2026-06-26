# -*- coding: utf-8 -*-
# 工单编号：人工智能NLP-Agent数字人项目-医疗智能体-挂号管理
import sqlite3, json, os
from config import DB_PATH


def get_conn():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"数据库不存在，请先运行 python data/init_db.py")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def execute_query(sql: str, params: list = None):
    """执行 SELECT，返回 (rows, error)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        rows = [dict(r) for r in cur.fetchall()]
        return rows, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def execute_write(sql: str, params: list = None):
    """执行 INSERT/UPDATE，支持多条语句用分号分隔，返回 (rowcount, error)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        # 支持多条SQL（book需要两步）
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        total = 0
        for stmt in statements:
            cur.execute(stmt, params or [])
            total += cur.rowcount
        conn.commit()
        return total, None
    except Exception as e:
        conn.rollback()
        return 0, str(e)
    finally:
        conn.close()


def get_schema():
    """获取当前数据库表结构"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    lines = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = ", ".join(f"{r[1]} {r[2]}" for r in cur.fetchall())
        lines.append(f"{t}({cols})")
    conn.close()
    return "\n".join(lines)
