# -*- coding: utf-8 -*-
"""
work_order_12 健康咨询 - 知识图谱构建器
从 medical.json 导入数据到 SQLite (模拟 Neo4j 图数据库)
工单编号：人工智能NLP-Agent数字人项目-12-健康咨询
"""
import json
import sqlite3
import os
from config import DB_PATH, JSON_PATH


def create_tables(conn):
    """创建节点表和边表 (模拟 Neo4j Node/Edge 结构)"""
    cursor = conn.cursor()
    
    # 节点表 (Nodes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            properties TEXT,
            name TEXT NOT NULL
        )
    """)
    
    # 边表 (Edges/Relationships)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            relation_cn TEXT,
            FOREIGN KEY (source_id) REFERENCES nodes(id),
            FOREIGN KEY (target_id) REFERENCES nodes(id)
        )
    """)
    
    # 创建索引加速查询
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation)")
    
    conn.commit()


def import_json_to_db(json_path, db_path):
    """从 medical.json 导入到 SQLite"""
    if not os.path.exists(json_path):
        print(f"❌ 未找到数据文件: {json_path}")
        return False
    
    print(f"📖 正在读取知识图谱数据: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    print(f"   解析到 {len(nodes)} 个实体节点, {len(edges)} 条关系边")
    
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    cursor = conn.cursor()
    
    # 清空旧数据 (重新导入)
    cursor.execute("DELETE FROM edges")
    cursor.execute("DELETE FROM nodes")
    
    # 插入节点
    for node in nodes:
        properties_json = json.dumps(node.get("properties", {}), ensure_ascii=False)
        name = node.get("properties", {}).get("name", node["id"])
        cursor.execute(
            "INSERT OR REPLACE INTO nodes (id, label, properties, name) VALUES (?, ?, ?, ?)",
            (node["id"], node["label"], properties_json, name)
        )
    
    # 插入边
    for edge in edges:
        cursor.execute(
            "INSERT INTO edges (source_id, target_id, relation, relation_cn) VALUES (?, ?, ?, ?)",
            (edge["from"], edge["to"], edge["relation"], edge.get("relation_cn", ""))
        )
    
    conn.commit()
    
    # 验证导入结果
    node_count = cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    
    print(f"✅ 知识图谱构建完成: {node_count} 个节点, {edge_count} 条关系")
    conn.close()
    return True


def build_knowledge_base():
    """构建知识库的便捷函数"""
    success = import_json_to_db(JSON_PATH, DB_PATH)
    if success:
        print(f"📁 数据库文件: {DB_PATH}")
    return success


if __name__ == "__main__":
    build_knowledge_base()
