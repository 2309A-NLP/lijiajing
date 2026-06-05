from pymilvus import connections, Collection

connections.connect(host='127.0.0.1', port='19530')
col = Collection('knowledge_base')
col.load()

print(f'总文档数: {col.num_entities}')

# 按角色统计
roles = ['律师', '心理医生', '投资分析师', '奶茶师', '虚拟朋友']
for r in roles:
    try:
        res = col.query(expr=f'role_type == "{r}"', limit=10000, output_fields=['role_type'])
        print(f'{r}: {len(res)} 条')
    except Exception as e:
        print(f'{r}: 查询失败 - {e}')