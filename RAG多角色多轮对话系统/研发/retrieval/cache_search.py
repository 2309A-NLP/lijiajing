# cache_search.py
import redis
import hashlib

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
            _redis_client.ping()
        except:
            _redis_client = None
    return _redis_client


def redis_search(query: str, top_k: int = 10):
    """Redis 缓存检索"""
    try:
        r = _get_redis()
        if r is None:
            return []

        # 生成缓存键
        cache_key = f"search_cache:{hashlib.md5(query.encode()).hexdigest()}"
        cached = r.get(cache_key)

        if cached:
            import json
            return json.loads(cached)
        return []
    except Exception as e:
        print(f"Redis检索失败: {e}")
        return []


def save_search_cache(query: str, results: list):
    """保存检索结果到缓存"""
    try:
        r = _get_redis()
        if r:
            import json
            cache_key = f"search_cache:{hashlib.md5(query.encode()).hexdigest()}"
            r.setex(cache_key, 3600, json.dumps(results))
    except:
        pass