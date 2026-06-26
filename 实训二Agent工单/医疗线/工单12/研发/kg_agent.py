# -*- coding: utf-8 -*-
"""
work_order_12 健康咨询 - 知识图谱 Agent
实现: Query 解析 -> 实体识别 -> Cypher/SQL 生成 -> 图谱查询 -> LLM 回答
工单编号：人工智能NLP-Agent数字人项目-12-健康咨询
"""
import json
import re
import sqlite3
import requests
from config import DB_PATH, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, SYSTEM_PROMPT, RELATION_MAP


class MedicalKGAgent:
    """医疗健康知识图谱 Agent"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.db = None
        self._connect_db()
    
    def _connect_db(self):
        """连接数据库"""
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
    
    def search_disease(self, query_text):
        """从用户 query 中识别疾病实体"""
        cursor = self.db.cursor()
        
        # 方法 1: 精确匹配
        cursor.execute("SELECT id, name, label FROM nodes WHERE name = ?", (query_text,))
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        # 方法 2: 模糊匹配 (包含关键词)
        keywords = self._extract_keywords(query_text)
        for kw in keywords:
            cursor.execute("SELECT id, name, label FROM nodes WHERE name LIKE ?", (f"%{kw}%",))
            result = cursor.fetchone()
            if result:
                return dict(result)
        
        # 方法 3: 症状反推疾病
        for kw in keywords:
            cursor.execute("""
                SELECT DISTINCT n1.id, n1.name, n1.label 
                FROM nodes n1 
                JOIN edges e ON n1.id = e.source_id 
                JOIN nodes n2 ON e.target_id = n2.id 
                WHERE n2.name LIKE ? AND e.relation = 'has_symptom'
            """, (f"%{kw}%",))
            result = cursor.fetchone()
            if result:
                return dict(result)
        
        return None
    
    def _extract_keywords(self, text):
        """提取查询关键词 (简化版 NER)"""
        # 医学关键词词典 (可扩展)
        disease_keywords = [
            "百日咳", "流感", "感冒", "胃炎", "肺炎", "腹泻", "头痛", "发热", "咳嗽", "腹痛"
        ]
        symptom_keywords = [
            "肚子疼", "头疼", "发烧", "咳嗽", "恶心", "呕吐", "乏力", "肌肉酸痛",
            "痉挛", "痉挛性", "鸡鸣", "呼吸困难", "窒息"
        ]
        
        found = []
        for kw in disease_keywords + symptom_keywords:
            if kw in text:
                found.append(kw)
        return found
    
    def query_relations(self, entity_id):
        """查询实体的所有关联关系 (模拟 Neo4j Cypher 查询)"""
        cursor = self.db.cursor()
        
        # SQL 查询模拟 Cypher: MATCH (d:Disease {name: X})-[r]->(n) RETURN r, n
        cursor.execute("""
            SELECT e.relation, e.relation_cn, n2.id, n2.name, n2.label, n2.properties
            FROM edges e
            JOIN nodes n1 ON e.source_id = n1.id
            JOIN nodes n2 ON e.target_id = n2.id
            WHERE n1.id = ?
        """, (entity_id,))
        
        results = []
        for row in cursor.fetchall():
            props = json.loads(row["properties"]) if row["properties"] else {}
            results.append({
                "relation": row["relation"],
                "relation_cn": row["relation_cn"],
                "target_name": row["name"],
                "target_label": row["label"],
                "properties": props
            })
        
        return results
    
    def query_by_relation_type(self, entity_id, relation_type):
        """按关系类型精确查询 (模拟特定 Cypher 查询)"""
        if relation_type not in RELATION_MAP:
            return []
        
        cursor = self.db.cursor()
        sql = RELATION_MAP[relation_type]["query"]
        cursor.execute(sql, (entity_id,))
        
        results = []
        for row in cursor.fetchall():
            props = json.loads(row["properties"]) if row["properties"] else {}
            results.append({"name": row["name"], "properties": props})
        
        return results
    
    def generate_answer(self, query, kg_results):
        """使用 LLM 基于知识图谱结果生成回答"""
        # 构建知识图谱上下文
        context_parts = []
        for item in kg_results:
            rel_name = item.get("relation_cn", item.get("relation", ""))
            target = item.get("target_name", "")
            props = item.get("properties", {})
            detail = ", ".join([f"{k}: {v}" for k, v in props.items()])
            context_parts.append(f"- {rel_name}: {target} ({detail})" if detail else f"- {rel_name}: {target}")
        
        kg_context = "\n".join(context_parts) if context_parts else "知识图谱中未找到相关信息"
        
        prompt = SYSTEM_PROMPT.format(kg_context=kg_context, query=query)
        
        try:
            response = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 512
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"[LLM 调用失败: {response.status_code}] 知识图谱结果: {kg_context}"
        except Exception as e:
            # 回退: 直接返回知识图谱原始数据
            return f"[LLM 不可用，直接返回图谱数据]\n{kg_context}"
    
    def ask(self, query):
        """完整问答流程: Query -> 实体识别 -> 图谱查询 -> LLM 回答"""
        print(f"\n{'='*50}")
        print(f"🔍 知识图谱 Agent 处理中: {query}")
        print(f"{'='*50}")
        
        # 步骤 1: 识别疾病实体
        print("📌 [步骤 1] 实体识别...")
        entity = self.search_disease(query)
        
        if not entity:
            print("   ⚠️  未在知识图谱中找到匹配的疾病实体")
            return self.generate_answer(query, [])
        
        print(f"   ✅ 识别到实体: {entity['name']} (类型: {entity['label']})")
        
        # 步骤 2: 查询知识图谱
        print("📌 [步骤 2] 生成知识图谱查询 (Cypher 模拟)...")
        kg_results = self.query_relations(entity["id"])
        print(f"   ✅ 查询到 {len(kg_results)} 条关联关系")
        
        for item in kg_results:
            print(f"      → {item['relation_cn']}: {item['target_name']}")
        
        # 步骤 3: LLM 生成回答
        print("📌 [步骤 3] 调用 LLM 生成回答...")
        answer = self.generate_answer(query, kg_results)
        
        return answer


def demo_test():
    """工单测试案例演示 (覆盖百日咳 10 个场景)"""
    agent = MedicalKGAgent()
    
    # 优化验证关键词，匹配 LLM 的自然语言生成习惯
    test_cases = [
        ("百日咳的致病病原体是什么？", "百日咳杆菌"),
        ("百日咳主要通过什么途径传播？", "飞沫传播"),
        ("百日咳最具特征性的临床表现是什么？", "鸡鸣样"),
        ("百日咳患者的血常规检查会呈现什么特征？", "白细胞"),
        ("百日咳西医治疗首选的抗生素是什么？", "红霉素"),
        ("百日咳最常见的严重并发症是什么？", "支气管肺炎"),
        ("中医治疗痉咳期百日咳的主方是什么？", "桑白皮汤"),
        ("百日咳患者的隔离期应持续多久？", "40天"),
        ("护理百日咳患儿时需特别注意防范什么紧急情况？", "窒息"),
        ("百日咳患者应避免食用哪类食物？", "海鲜"),
    ]
    
    print("\n" + "="*60)
    print("🧪 工单 12 测试案例 - 百日咳场景覆盖")
    print("="*60)
    
    for i, (query, expected_keyword) in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}/10 ---")
        print(f"❓ 问: {query}")
        answer = agent.ask(query)
        print(f"💬 答: {answer}")
        
        # 智能验证：去除干扰字符后匹配
        clean_answer = answer.replace(" ", "").replace("\n", "")
        clean_keyword = expected_keyword.replace(" ", "").replace("\n", "")
        if clean_keyword in clean_answer:
            print(f"✅ 命中预期关键词: {expected_keyword}")
        else:
            print(f"⚠️  未命中预期关键词: {expected_keyword}")
    
    agent.close()


if __name__ == "__main__":
    demo_test()
