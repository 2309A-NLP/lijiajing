"""
工单12 - LightRAG优化
轻量级RAG优化策略
"""
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class LightRAG:
    """轻量级RAG优化"""
    
    def __init__(self):
        self.cache = {}  # 查询缓存
        self.cache_hits = 0
        self.cache_misses = 0
    
    def cache_query(self, query, result, ttl=3600):
        """查询缓存"""
        query_key = self._normalize(query)
        self.cache[query_key] = {
            "result": result,
            "timestamp": time.time(),
            "ttl": ttl
        }
    
    def get_from_cache(self, query):
        """从缓存获取"""
        query_key = self._normalize(query)
        if query_key in self.cache:
            entry = self.cache[query_key]
            if time.time() - entry["timestamp"] < entry["ttl"]:
                self.cache_hits += 1
                return entry["result"]
        self.cache_misses += 1
        return None
    
    def _normalize(self, query):
        """查询标准化"""
        import re
        normalized = re.sub(r'[\s,，。？！]+', ' ', query)
        return normalized.strip().lower()
    
    def cache_stats(self):
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total * 100 if total > 0 else 0
        return {
            "cache_size": len(self.cache),
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": round(hit_rate, 2)
        }
    
    @staticmethod
    def optimize_chunk_selection(query, chunks, max_chunks=3):
        """智能chunk选择"""
        import re
        
        # 查询关键词
        query_tokens = set(re.findall(r'[\u4e00-\u9fff\w]+', query))
        
        scored = []
        for chunk in chunks:
            chunk_tokens = set(re.findall(r'[\u4e00-\u9fff\w]+', chunk["text"]))
            overlap = len(query_tokens & chunk_tokens)
            score = overlap / len(query_tokens) if query_tokens else 0
            scored.append((score, chunk))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:max_chunks]]
    
    @staticmethod
    def streaming_generate(query, context, llm_func, chunk_size=100):
        """流式生成（模拟）"""
        prompt = f"""问题：{query}
        
上下文：{context[:2000]}

回答："""
        
        result = llm_func(prompt) if llm_func else "[流式生成待LLM接入]"
        
        # 模拟流式输出
        for i in range(0, len(result), chunk_size):
            yield result[i:i+chunk_size]

class RagOptimizer:
    """RAG综合优化器"""
    
    def __init__(self):
        self.techniques = {
            "query_caching": True,
            "chunk_pruning": True,
            "hybrid_search": True,
            "prompt_compression": True,
            "async_retrieval": False
        }
    
    def enable(self, technique):
        if technique in self.techniques:
            self.techniques[technique] = True
    
    def disable(self, technique):
        if technique in self.techniques:
            self.techniques[technique] = False
    
    def get_status(self):
        enabled = [k for k, v in self.techniques.items() if v]
        disabled = [k for k, v in self.techniques.items() if not v]
        return {"enabled": enabled, "disabled": disabled}

if __name__ == "__main__":
    # 测试LightRAG
    light = LightRAG()
    
    result = {"answer": "这是一个测试回答"}
    light.cache_query("武汉兴图新科的注册资本是多少？", result)
    
    cached = light.get_from_cache("武汉兴图新科的注册资本是多少？")
    print(f"缓存命中: {cached is not None}")
    print(f"缓存统计: {light.cache_stats()}")
    
    # 优化器
    optimizer = RagOptimizer()
    print(f"\n优化技术: {optimizer.get_status()}")
