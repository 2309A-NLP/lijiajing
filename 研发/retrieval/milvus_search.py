# milvus_search.py
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
import os

# 全局变量
_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        model_path = r"D:\2309A nlp 上课软件\BGE-m3\bge-m3"
        _model = SentenceTransformer(model_path)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        connections.connect(host='127.0.0.1', port='19530')
        _collection = Collection("knowledge_base")
        _collection.load()
    return _collection


def search_milvus(query: str, role: str = None, top_k: int = 10):
    """Milvus 向量检索"""
    try:
        model = _get_model()
        col = _get_collection()

        # 向量化查询
        query_emb = model.encode([query], normalize_embeddings=True)[0]

        # 构建过滤条件
        expr = None
        if role and role != "虚拟朋友":
            expr = f'role_type == "{role}"'

        # 检索
        results = col.search(
            data=[query_emb.tolist()],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=top_k,
            expr=expr,
            output_fields=["text", "role_type"]
        )

        formatted = []
        for hits in results:
            for hit in hits:
                formatted.append({
                    "text": hit.entity.get("text"),
                    "score": float(hit.score),
                    "source": "milvus"
                })
        return formatted
    except Exception as e:
        print(f"Milvus检索失败: {e}")
        return []