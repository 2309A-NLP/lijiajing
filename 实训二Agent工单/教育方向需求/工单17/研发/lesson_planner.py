# -*- coding: utf-8 -*-
"""
智能备课系统 - 核心逻辑
基于 LLM 的课程大纲生成、资源推荐、课件编排、目标对齐
"""
import json
from typing import Dict, List


class LessonPlanner:
    """智能备课 Agent"""
    
    # Bloom 教育目标分类
    BLOOM_LEVELS = ["记忆", "理解", "应用", "分析", "评价", "创造"]
    
    # 模拟教学资源库
    RESOURCE_DB = {
        "数学": [
            {"title": "高中数学必修一知识点总结", "type": "文档", "url": "#"},
            {"title": "函数图像动态演示", "type": "视频", "url": "#"},
            {"title": "高考真题精选100道", "type": "题库", "url": "#"},
        ],
        "语文": [
            {"title": "古诗词鉴赏技巧", "type": "文档", "url": "#"},
            {"title": "鲁迅作品深度解读", "type": "视频", "url": "#"},
            {"title": "作文素材积累手册", "type": "文档", "url": "#"},
        ],
        "英语": [
            {"title": "高考英语3500词", "type": "文档", "url": "#"},
            {"title": "听力训练MP3合集", "type": "音频", "url": "#"},
            {"title": "语法专项练习", "type": "题库", "url": "#"},
        ],
        "物理": [
            {"title": "力学实验视频合集", "type": "视频", "url": "#"},
            {"title": "物理公式速查表", "type": "文档", "url": "#"},
            {"title": "电磁学动画演示", "type": "动画", "url": "#"},
        ],
        "化学": [
            {"title": "元素周期表记忆法", "type": "文档", "url": "#"},
            {"title": "有机化学反应机理", "type": "视频", "url": "#"},
            {"title": "实验操作规范指南", "type": "文档", "url": "#"},
        ],
    }
    
    def generate_outline(self, topic: str, subject: str, grade: str, hours: int = 2) -> Dict:
        """生成课程大纲"""
        outline = {
            "topic": topic,
            "subject": subject,
            "grade": grade,
            "total_hours": hours,
            "objectives": self._generate_objectives(topic, subject),
            "structure": self._generate_structure(topic, hours),
            "key_points": self._generate_key_points(topic, subject),
            "difficulties": self._generate_difficulties(topic, subject),
        }
        return outline
    
    def recommend_resources(self, subject: str, topic: str) -> List[Dict]:
        """推荐教学资源"""
        base_resources = self.RESOURCE_DB.get(subject, self.RESOURCE_DB["数学"])
        # 模拟智能推荐：根据主题过滤
        recommended = []
        for r in base_resources:
            recommended.append({
                **r,
                "relevance": "高",
                "reason": f"与「{topic}」知识点高度相关"
            })
        return recommended[:3]
    
    def arrange_courseware(self, outline: Dict) -> Dict:
        """课件自动编排"""
        structure = outline["structure"]
        courseware = {
            "slides": [],
            "total_pages": len(structure) * 3 + 5,  # 每节3页 + 封面/目录/总结
            "estimated_time": f"{outline['total_hours'] * 45}分钟",
        }
        
        # 生成幻灯片结构
        courseware["slides"].append({"type": "封面", "title": outline["topic"], "page": 1})
        courseware["slides"].append({"type": "目录", "title": "课程结构", "page": 2})
        
        page = 3
        for i, section in enumerate(structure, 1):
            courseware["slides"].append({
                "type": "章节",
                "title": f"{i}. {section['title']}",
                "page": page,
                "duration": f"{section['minutes']}分钟"
            })
            page += 3
        
        courseware["slides"].append({"type": "总结", "title": "知识梳理", "page": page})
        courseware["slides"].append({"type": "作业", "title": "课后练习", "page": page + 1})
        
        return courseware
    
    def check_alignment(self, outline: Dict, target_levels: List[str] = None) -> Dict:
        """教学目标对齐检查（Bloom分类法）"""
        if target_levels is None:
            target_levels = ["理解", "应用", "分析"]
        
        objectives = outline["objectives"]
        alignment = {
            "target_levels": target_levels,
            "covered_levels": [],
            "missing_levels": [],
            "alignment_score": 0,
            "suggestions": []
        }
        
        # 检查每个目标对应的Bloom层级
        covered = set()
        for obj in objectives:
            for level in target_levels:
                if level in obj or self._infer_bloom_level(obj) == level:
                    covered.add(level)
        
        alignment["covered_levels"] = list(covered)
        alignment["missing_levels"] = [l for l in target_levels if l not in covered]
        alignment["alignment_score"] = len(covered) / len(target_levels) * 100
        
        if alignment["missing_levels"]:
            alignment["suggestions"].append(
                f"建议增加「{'、'.join(alignment['missing_levels'])}」层级的教学目标"
            )
        
        return alignment
    
    def _generate_objectives(self, topic: str, subject: str) -> List[str]:
        """生成教学目标"""
        return [
            f"理解{topic}的基本概念和原理",
            f"掌握{topic}的核心知识点",
            f"能够应用{topic}解决实际问题",
            f"分析{topic}在不同场景下的应用",
        ]
    
    def _generate_structure(self, topic: str, hours: int) -> List[Dict]:
        """生成课程结构"""
        base_structure = [
            {"title": "导入与背景", "minutes": 10},
            {"title": f"{topic}核心概念", "minutes": 20},
            {"title": "案例分析与讨论", "minutes": 15},
            {"title": "实践练习", "minutes": 15},
            {"title": "总结与作业", "minutes": 10},
        ]
        return base_structure
    
    def _generate_key_points(self, topic: str, subject: str) -> List[str]:
        """生成重点"""
        return [
            f"{topic}的定义与内涵",
            f"{topic}的核心公式/原理",
            f"{topic}的典型应用场景",
        ]
    
    def _generate_difficulties(self, topic: str, subject: str) -> List[str]:
        """生成难点"""
        return [
            f"{topic}的抽象概念理解",
            f"{topic}在实际问题中的应用",
        ]
    
    def _infer_bloom_level(self, objective: str) -> str:
        """推断教学目标对应的Bloom层级"""
        keywords = {
            "记忆": ["记住", "识别", "列举"],
            "理解": ["理解", "解释", "描述"],
            "应用": ["应用", "使用", "解决"],
            "分析": ["分析", "比较", "区分"],
            "评价": ["评价", "判断", "批判"],
            "创造": ["创造", "设计", "构建"],
        }
        for level, kws in keywords.items():
            if any(kw in objective for kw in kws):
                return level
        return "理解"  # 默认


# 单例
planner = LessonPlanner()
