# hybrid_search.py
import pymysql

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "rag_system",
    "charset": "utf8mb4"
}


def mysql_search(query: str, top_k: int = 10):
    """MySQL 关键词检索"""
    results = []
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # 简单的 LIKE 检索
        keywords = query.split()[:3]
        for kw in keywords:
            cursor.execute(
                "SELECT response FROM chat_logs WHERE message LIKE %s OR response LIKE %s LIMIT %s",
                (f"%{kw}%", f"%{kw}%", top_k)
            )
            for row in cursor.fetchall():
                if row[0]:
                    results.append({
                        "text": row[0],
                        "score": 0.5,
                        "source": "mysql"
                    })
        conn.close()

        # 去重
        seen = set()
        unique = []
        for r in results:
            if r["text"] not in seen:
                seen.add(r["text"])
                unique.append(r)
        return unique[:top_k]
    except Exception as e:
        print(f"MySQL检索失败: {e}")
        return []