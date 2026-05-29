# bm25_search.py - BM25 关键词检索引擎
import jieba
import pickle
import os
from typing import List, Dict


class BM25Search:
    def __init__(self, cache_path="bm25_cache.pkl"):
        self.cache_path = cache_path
        self.bm25 = None
        self.corpus = []
        self._load_cache()

    def _tokenize(self, text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))

    def build_index(self, texts: List[str]):
        """构建 BM25 索引"""
        from rank_bm25 import BM25Okapi
        self.corpus = texts
        tokenized_corpus = [self._tokenize(str(t)) for t in texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._save_cache()
        print(f"✅ BM25 索引构建完成，共 {len(texts)} 条文档")

    def _save_cache(self):
        """保存索引到本地缓存"""
        with open(self.cache_path, 'wb') as f:
            pickle.dump({"corpus": self.corpus, "bm25": self.bm25}, f)

    def _load_cache(self):
        """加载本地缓存"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'rb') as f:
                    data = pickle.load(f)
                    self.corpus = data["corpus"]
                    self.bm25 = data["bm25"]
                print(f"✅ BM25 缓存加载成功，共 {len(self.corpus)} 条文档")
            except:
                pass

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """BM25 检索"""
        if not self.bm25:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # 获取 top_k 索引
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for i in top_indices:
            if scores[i] > 0:
                results.append({
                    "text": self.corpus[i],
                    "score": float(scores[i]),
                    "source": "bm25"
                })
        return results


# 全局实例
bm25_search_engine = BM25Search()


def search_bm25(query: str, top_k: int = 10) -> List[Dict]:
    """BM25 检索入口函数"""
    return bm25_search_engine.search(query, top_k)


def build_bm25_index_from_kb():
    """从 Milvus 知识库构建 BM25 索引"""
    from pymilvus import Collection
    from pymilvus import connections

    connections.connect(host="127.0.0.1", port="19530")
    col = Collection("knowledge_base")
    col.load()

    # 查询所有文本
    results = col.query(expr="id >= 0", output_fields=["text"], limit=10000)
    texts = [r["text"] for r in results if r.get("text")]

    bm25_search_engine.build_index(texts)
    print(f"✅ BM25 索引已构建，共 {len(texts)} 条文档")