# ============================================
# 互联网搜索召回模块
# 功能：通过 DuckDuckGo API 实时搜索互联网内容
# 说明：该引擎在中国大陆需代理访问，配置 proxies 参数即可激活
# ============================================

import requests
import json

def search_web(query, num=3):
    """
    互联网搜索函数
    参数：
        query: 用户搜索词
        num: 返回结果数量，默认3条
    返回：
        包含 text（摘要）和 source（来源）的字典列表
    工作原理：
        向 DuckDuckGo API 发送 GET 请求
        解析返回的 JSON 中的 RelatedTopics 字段
        提取每条结果的 Text（摘要）和 FirstURL（链接）
    """
    try:
        # 调用 DuckDuckGo 免费搜索 API（无需 API Key）
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,           # 搜索关键词
                "format": "json",     # 要求返回 JSON 格式
                "no_html": 1,         # 去除 HTML 标签
                "skip_disambig": 1    # 跳过消歧义页面
            },
            timeout=8                 # 超时 8 秒避免长时间等待
        )
        data = resp.json()            # 解析 JSON 响应
        results = []
        # 遍历 RelatedTopics 提取搜索结果
        for item in data.get("RelatedTopics", [])[:num]:
            if item.get("Text"):
                results.append({
                    "text": item["Text"],           # 搜索结果摘要
                    "source": "互联网",              # 标记来源为互联网
                    "url": item.get("FirstURL", "")  # 结果的 URL 链接
                })
        # 如果有结果就返回，否则返回未找到提示
        return results if results else [{"text": "未找到相关搜索结果", "source": "互联网"}]
    except:
        # 搜索失败时返回不可用提示
        return [{"text": "搜索服务暂不可用", "source": "互联网"}]

print("互联网搜索模块就绪")