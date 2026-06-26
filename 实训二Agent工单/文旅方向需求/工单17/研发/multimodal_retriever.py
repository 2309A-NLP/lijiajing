# -*- coding: utf-8 -*-
"""
文旅智能体 - 多模态知识检索系统
支持图片检索、文本检索、多模态融合检索
"""
import random
from typing import Dict, List


class MultimodalRetriever:
    """多模态知识检索 Agent"""
    
    # 模拟文旅知识库
    KNOWLEDGE_BASE = [
        # 北京景点
        {
            "id": "001",
            "title": "故宫太和殿",
            "type": "建筑",
            "description": "明清两代皇家宫殿，世界文化遗产",
            "tags": ["古建筑", "皇家", "北京", "世界遗产", "宫殿"],
            "image_url": "https://example.com/gugong.jpg",
            "embedding": [0.1, 0.2, 0.3, 0.4],
        },
        {
            "id": "002",
            "title": "长城烽火台",
            "type": "建筑",
            "description": "古代军事防御工程，中华民族象征",
            "tags": ["古建筑", "军事", "北京", "世界遗产", "长城"],
            "image_url": "https://example.com/changcheng.jpg",
            "embedding": [0.2, 0.3, 0.4, 0.5],
        },
        {
            "id": "003",
            "title": "国家图书馆",
            "type": "文化设施",
            "description": "中国最大的图书馆，亚洲规模最大的图书馆之一",
            "tags": ["图书馆", "北京", "文化", "学习", "古籍"],
            "image_url": "https://example.com/nlc.jpg",
            "embedding": [0.7, 0.8, 0.9, 1.0],
        },
        {
            "id": "004",
            "title": "首都图书馆",
            "type": "文化设施",
            "description": "北京市级公共图书馆，藏书丰富",
            "tags": ["图书馆", "北京", "公共", "阅读", "学习"],
            "image_url": "https://example.com/clc.jpg",
            "embedding": [0.75, 0.85, 0.95, 1.0],
        },
        {
            "id": "005",
            "title": "北京大学图书馆",
            "type": "文化设施",
            "description": "中国高校图书馆的代表，历史悠久",
            "tags": ["图书馆", "北京", "高校", "学术", "北大"],
            "image_url": "https://example.com/pku.jpg",
            "embedding": [0.8, 0.9, 1.0, 1.0],
        },
        # 杭州景点
        {
            "id": "006",
            "title": "西湖断桥",
            "type": "景观",
            "description": "杭州西湖著名景点，白蛇传说发生地",
            "tags": ["自然景观", "传说", "杭州", "湖泊", "西湖"],
            "image_url": "https://example.com/xihu.jpg",
            "embedding": [0.3, 0.4, 0.5, 0.6],
        },
        {
            "id": "007",
            "title": "杭州图书馆",
            "type": "文化设施",
            "description": "杭州市公共图书馆，以免费开放闻名",
            "tags": ["图书馆", "杭州", "公共", "免费", "阅读"],
            "image_url": "https://example.com/hzlib.jpg",
            "embedding": [0.72, 0.82, 0.92, 1.0],
        },
        # 西安景点
        {
            "id": "008",
            "title": "兵马俑",
            "type": "文物",
            "description": "秦始皇陵兵马俑，世界第八大奇迹",
            "tags": ["文物", "秦朝", "西安", "世界遗产", "兵马俑"],
            "image_url": "https://example.com/bmy.jpg",
            "embedding": [0.4, 0.5, 0.6, 0.7],
        },
        {
            "id": "009",
            "title": "陕西省图书馆",
            "type": "文化设施",
            "description": "陕西省省级公共图书馆",
            "tags": ["图书馆", "西安", "陕西", "公共", "古籍"],
            "image_url": "https://example.com/sxlib.jpg",
            "embedding": [0.73, 0.83, 0.93, 1.0],
        },
        # 敦煌
        {
            "id": "010",
            "title": "敦煌莫高窟",
            "type": "艺术",
            "description": "佛教艺术宝库，丝绸之路明珠",
            "tags": ["艺术", "佛教", "敦煌", "壁画", "世界遗产"],
            "image_url": "https://example.com/mogaoku.jpg",
            "embedding": [0.5, 0.6, 0.7, 0.8],
        },
        # 苏州
        {
            "id": "011",
            "title": "苏州园林",
            "type": "建筑",
            "description": "江南古典园林代表，世界文化遗产",
            "tags": ["古建筑", "园林", "苏州", "世界遗产", "江南"],
            "image_url": "https://example.com/suzhou.jpg",
            "embedding": [0.6, 0.7, 0.8, 0.9],
        },
        {
            "id": "012",
            "title": "苏州图书馆",
            "type": "文化设施",
            "description": "苏州市公共图书馆，古籍收藏丰富",
            "tags": ["图书馆", "苏州", "古籍", "江南", "公共"],
            "image_url": "https://example.com/szlib.jpg",
            "embedding": [0.74, 0.84, 0.94, 1.0],
        },
    ]
    
    def search_by_text(self, query: str, top_k: int = 3) -> List[Dict]:
        """文本检索"""
        results = []
        query_lower = query.lower()
        
        # 简单的中文分词（按常见分隔符）
        keywords = self._tokenize(query_lower)
        
        for item in self.KNOWLEDGE_BASE:
            score = 0
            title_lower = item["title"].lower()
            desc_lower = item["description"].lower()
            
            # 关键词匹配
            for kw in keywords:
                if not kw:
                    continue
                # 标题匹配（权重高）
                if kw in title_lower:
                    score += 0.4
                # 描述匹配
                if kw in desc_lower:
                    score += 0.2
                # 标签匹配
                for tag in item["tags"]:
                    if kw in tag.lower():
                        score += 0.3
                        break
            
            if score > 0:
                results.append({
                    **item,
                    "score": min(score, 1.0),
                    "match_type": "text"
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        """简单的中文分词"""
        # 移除常见停用词和分隔符
        separators = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这']
        result = text
        for sep in separators:
            result = result.replace(sep, ' ')
        # 按空格分割
        tokens = [t.strip() for t in result.split() if t.strip()]
        # 如果分词后为空，返回原词
        return tokens if tokens else [text]
    
    def search_by_image(self, image_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """图片检索（以图搜图）"""
        results = []
        
        for item in self.KNOWLEDGE_BASE:
            # 计算余弦相似度（简化版）
            similarity = self._cosine_similarity(image_embedding, item["embedding"])
            results.append({
                **item,
                "score": similarity,
                "match_type": "image"
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def multimodal_search(self, text_query: str, image_embedding: List[float] = None, top_k: int = 3) -> List[Dict]:
        """多模态融合检索"""
        text_results = self.search_by_text(text_query, top_k=top_k * 2)
        
        if image_embedding:
            image_results = self.search_by_image(image_embedding, top_k=top_k * 2)
            
            # 融合排序
            combined = {}
            for item in text_results:
                combined[item["id"]] = {
                    **item,
                    "text_score": item["score"],
                    "image_score": 0
                }
            
            for item in image_results:
                if item["id"] in combined:
                    combined[item["id"]]["image_score"] = item["score"]
                else:
                    combined[item["id"]] = {
                        **item,
                        "text_score": 0,
                        "image_score": item["score"]
                    }
            
            # 加权融合（文本0.4，图片0.6）
            final_results = []
            for item in combined.values():
                final_score = item["text_score"] * 0.4 + item["image_score"] * 0.6
                final_results.append({
                    **item,
                    "score": final_score,
                    "match_type": "multimodal"
                })
            
            final_results.sort(key=lambda x: x["score"], reverse=True)
            return final_results[:top_k]
        else:
            return text_results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_stats(self) -> Dict:
        """获取知识库统计"""
        type_count = {}
        for item in self.KNOWLEDGE_BASE:
            t = item["type"]
            type_count[t] = type_count.get(t, 0) + 1
        
        return {
            "total_items": len(self.KNOWLEDGE_BASE),
            "type_distribution": type_count,
            "supported_modalities": ["text", "image", "multimodal"]
        }


# 单例
retriever = MultimodalRetriever()
