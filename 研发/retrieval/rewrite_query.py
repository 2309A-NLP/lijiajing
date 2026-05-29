# cat > /opt/deeprole/查询改写器.py << 'EOF'
# ============================================
# 【查询改写器】- 用大模型优化用户提问
# 位置：用户提问后、检索之前
# 用途：把口语化问题改写成更适合向量检索的标准表达
# ============================================

import requests

def rewrite_query(original_query, persona, role_type):
    """
    查询改写函数
    参数：original_query=用户原始问题, persona=人格, role_type=角色
    返回：改写后的多个查询列表
    """
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": "Bearer sk-15ef03506ce14a02ab99d468ba5b2f8f",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{
                    "role": "system",
                    "content": f"你是{role_type}，把用户问题改写成3个不同角度的检索查询，每行一个。"
                }, {
                    "role": "user",
                    "content": original_query
                }],
                "temperature": 0.7
            },
            timeout=10
        )
        content = resp.json()["choices"][0]["message"]["content"]
        queries = [q.strip() for q in content.split('\n') if q.strip()]
        return queries[:3] if queries else [original_query]
    except:
        return [original_query]

print("查询改写器就绪")
EOF