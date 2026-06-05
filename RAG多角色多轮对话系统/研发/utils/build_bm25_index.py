# build_bm25_index.py - 从 Milvus 构建 BM25 索引
from pymilvus import connections, Collection
from bm25_search import bm25_search_engine


def build_bm25_index():
    print("🔨 开始构建 BM25 索引...")
    try:
        connections.connect(host='127.0.0.1', port='19530')
        col = Collection("knowledge_base")
        col.load()

        # 查询所有文本
        results = col.query(expr="id >= 0", output_fields=["text"], limit=20000)
        texts = [r["text"] for r in results if r.get("text")]

        print(f"📚 从 Milvus 读取到 {len(texts)} 条文档")

        # 构建 BM25 索引
        bm25_search_engine.build_index(texts)
        print("✅ BM25 索引构建完成")

    except Exception as e:
        print(f"❌ BM25 索引构建失败: {e}")


if __name__ == "__main__":
    build_bm25_index()