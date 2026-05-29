# multi_recall.py - 多路召回融合（带缓存）
import hashlib
import json
import redis
from typing import List, Dict
from milvus_search import search_milvus
from hybrid_search import mysql_search
from bm25_search import search_bm25
from cache_search import redis_search


class MultiPathRetriever:
    def __init__(self):
        self.weights = {
            "milvus": 0.5,
            "bm25": 0.3,
            "mysql": 0.1,
            "redis": 0.1
        }
        # 初始化 Redis 客户端
        try:
            self.redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
            print("✅ Redis 缓存已启用")
        except:
            self.redis_client = None
            self.redis_available = False
            print("⚠️ Redis 不可用，缓存功能禁用")

    def reciprocal_rank_fusion(self, results_list: dict, k: int = 60):
        """RRF 融合算法"""
        scores = {}
        for source, results in results_list.items():
            for rank, r in enumerate(results[:10], 1):
                rrf_score = self.weights.get(source, 0.1) / (k + rank)
                key = r.get("text", "")[:100]
                if key not in scores:
                    scores[key] = {
                        "text": r["text"],
                        "score": rrf_score,
                        "sources": [source]
                    }
                else:
                    scores[key]["score"] += rrf_score
                    scores[key]["sources"].append(source)

        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results

    def search(self, query: str, role: str = None, top_k: int = 5) -> List[Dict]:
        # ========== 1. 检查缓存 ==========
        if self.redis_available:
            try:
                cache_key = f"recall:{hashlib.md5(f'{query}_{role}'.encode()).hexdigest()}"
                cached = self.redis_client.get(cache_key)
                if cached:
                    print(f"💡 缓存命中: {query[:30]}...")
                    return json.loads(cached)
            except Exception as e:
                print(f"缓存读取失败: {e}")

        # ========== 2. 多路召回 ==========
        print(f"\n🔍 多路召回: {query[:50]}...")

        # 并行召回
        results_milvus = search_milvus(query, role, top_k=10)
        results_bm25 = search_bm25(query, top_k=10)
        results_mysql = mysql_search(query, top_k=5)
        results_redis = redis_search(query, top_k=3)

        print(f"  Milvus: {len(results_milvus)}条")
        print(f"  BM25: {len(results_bm25)}条")
        print(f"  MySQL: {len(results_mysql)}条")
        print(f"  Redis: {len(results_redis)}条")

        all_results = {
            "milvus": results_milvus,
            "bm25": results_bm25,
            "mysql": results_mysql,
            "redis": results_redis
        }

        # RRF 融合
        fused = self.reciprocal_rank_fusion(all_results)
        final_results = fused[:top_k]

        # ========== 3. 保存到缓存 ==========
        if self.redis_available and final_results:
            try:
                cache_key = f"recall:{hashlib.md5(f'{query}_{role}'.encode()).hexdigest()}"
                self.redis_client.setex(cache_key, 3600, json.dumps(final_results))
                print(f"💾 已缓存: {query[:30]}...")
            except Exception as e:
                print(f"缓存保存失败: {e}")

        return final_results


# 全局实例
retriever = MultiPathRetriever()


def multi_path_search(query: str, role: str = None, top_k: int = 5) -> List[Dict]:
    """多路召回统一入口"""
    return retriever.search(query, role, top_k)