# 工单编号：人工智能NLP-Agent数字人项目-18-智能导览
"""
文旅智能体 - 智能导览
功能：语音导览生成、LBS位置感知推荐、景点文化解说、个性化游览路线
"""
import json
from typing import Dict, List
from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

# ───────── 模拟景点知识库 ─────────
SCENIC_SPOTS = {
    "故宫": {
        "name": "故宫博物院",
        "location": {"lat": 39.9163, "lng": 116.3972},
        "description": "明清两代皇家宫殿，世界文化遗产",
        "history": "建于明永乐四年(1406年)，历时14年建成，是明清两代24位皇帝的皇宫",
        "highlights": ["太和殿", "中和殿", "保和殿", "乾清宫", "御花园"],
        "visit_time": "3-4小时",
        "ticket": "60元"
    },
    "长城": {
        "name": "八达岭长城",
        "location": {"lat": 40.3539, "lng": 116.0156},
        "description": "世界文化遗产，中华民族象征",
        "history": "始建于春秋战国时期，明朝大规模修缮，全长8851.8公里",
        "highlights": ["好汉坡", "烽火台", "敌楼", "城墙"],
        "visit_time": "4-5小时",
        "ticket": "40元"
    },
    "西湖": {
        "name": "杭州西湖",
        "location": {"lat": 30.2420, "lng": 120.1486},
        "description": "人间天堂，世界文化遗产",
        "history": "西湖形成于距今约2000年前，历代文人墨客留下无数诗篇",
        "highlights": ["断桥", "苏堤", "白堤", "三潭印月", "雷峰塔"],
        "visit_time": "4-6小时",
        "ticket": "免费"
    },
    "兵马俑": {
        "name": "秦始皇兵马俑",
        "location": {"lat": 34.3841, "lng": 109.2785},
        "description": "世界第八大奇迹",
        "history": "建于公元前246年至前208年，是秦始皇陵的陪葬坑",
        "highlights": ["一号坑", "二号坑", "三号坑", "铜车马馆"],
        "visit_time": "3-4小时",
        "ticket": "120元"
    }
}

# ───────── 游览路线模板 ─────────
TOUR_ROUTES = {
    "北京经典一日游": [
        {"spot": "故宫", "time": "09:00-12:00", "duration": "3小时"},
        {"spot": "景山公园", "time": "12:30-14:00", "duration": "1.5小时"},
        {"spot": "南锣鼓巷", "time": "14:30-16:00", "duration": "1.5小时"},
        {"spot": "什刹海", "time": "16:30-18:00", "duration": "1.5小时"}
    ],
    "杭州西湖一日游": [
        {"spot": "断桥", "time": "08:00-09:00", "duration": "1小时"},
        {"spot": "白堤", "time": "09:00-10:00", "duration": "1小时"},
        {"spot": "孤山", "time": "10:00-11:30", "duration": "1.5小时"},
        {"spot": "苏堤", "time": "13:00-14:30", "duration": "1.5小时"},
        {"spot": "三潭印月", "time": "15:00-16:30", "duration": "1.5小时"}
    ]
}

# ───────── Prompt ─────────
SYSTEM_PROMPT = """你是「智能导览」，为游客提供景区导览服务。

【能力】
1. 景点文化解说：介绍景点历史、文化、特色
2. 游览路线推荐：根据时间和兴趣推荐路线
3. LBS位置推荐：根据位置推荐附近景点

【回答规范】
- 语言生动有趣，像导游讲解
- 包含历史故事和文化背景
- 给出实用建议（游览时间、注意事项）

【景点知识库】
{knowledge}
"""

# ───────── 工具函数 ─────────

def search_spot(spot_name: str) -> Dict:
    """搜索景点信息"""
    for name, info in SCENIC_SPOTS.items():
        if spot_name in name or name in spot_name:
            return info
    return {"error": f"未找到景点: {spot_name}"}


def generate_commentary(spot_name: str) -> str:
    """生成景点解说词"""
    spot_info = search_spot(spot_name)
    if "error" in spot_info:
        return spot_info["error"]
    
    knowledge_text = json.dumps(spot_info, ensure_ascii=False, indent=2)
    system = SYSTEM_PROMPT.format(knowledge=knowledge_text)
    
    prompt = f"请为游客介绍{spot_name}，包括历史背景、文化特色、游览建议"
    
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[LLM调用失败: {e}]\n\n景点信息：{json.dumps(spot_info, ensure_ascii=False)}"


def recommend_route(duration: str = "一日", interest: str = "文化") -> List[Dict]:
    """推荐游览路线"""
    # 简单匹配
    for route_name, spots in TOUR_ROUTES.items():
        if duration in route_name:
            return {"route_name": route_name, "spots": spots}
    
    # 默认返回北京路线
    return {"route_name": "北京经典一日游", "spots": TOUR_ROUTES["北京经典一日游"]}


def nearby_recommendation(lat: float, lng: float, radius: float = 5.0) -> List[Dict]:
    """LBS附近景点推荐"""
    nearby = []
    for name, info in SCENIC_SPOTS.items():
        # 简单距离计算（实际应该用 Haversine 公式）
        spot_lat = info["location"]["lat"]
        spot_lng = info["location"]["lng"]
        distance = ((spot_lat - lat) ** 2 + (spot_lng - lng) ** 2) ** 0.5 * 111  # 近似公里数
        
        if distance <= radius:
            nearby.append({
                "name": name,
                "distance": f"{distance:.1f}km",
                "description": info["description"]
            })
    
    nearby.sort(key=lambda x: float(x["distance"].replace("km", "")))
    return nearby if nearby else [{"message": f"半径{radius}km内未找到景点"}]


def generate_audio_script(spot_name: str, language: str = "中文") -> str:
    """生成语音导览脚本"""
    spot_info = search_spot(spot_name)
    if "error" in spot_info:
        return spot_info["error"]
    
    script = f"""
🎙️ 语音导览脚本 - {spot_name}

【开场】
各位游客朋友们，大家好！欢迎来到{spot_info['name']}。

【景点介绍】
{spot_info['description']}。
{spot_info['history']}。

【重点看点】
接下来请大家跟随我，一起参观：
{chr(10).join(['• ' + h for h in spot_info['highlights']])}

【游览建议】
建议游览时间：{spot_info['visit_time']}
门票价格：{spot_info['ticket']}

【结束语】
希望大家在这里度过愉快的时光！
"""
    return script


# ───────── Agent 类 ─────────

class GuideAgent:
    def __init__(self):
        self.history: list = []
        self.call_log: list = []
        self._greeted = False
    
    def reset(self):
        self.history = []
        self.call_log = []
        self._greeted = False
    
    def chat(self, user_input: str) -> str:
        """处理用户输入"""
        from datetime import datetime
        
        # 简单意图识别
        if "路线" in user_input or "怎么游" in user_input:
            # 推荐路线
            route = recommend_route("一日", "文化")
            reply = f"🗺️ 推荐路线：{route['route_name']}\n\n"
            for i, spot in enumerate(route['spots'], 1):
                reply += f"{i}. {spot['spot']} ({spot['time']}, {spot['duration']})\n"
            self.call_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": "recommend_route",
                "result": route['route_name']
            })
            return reply
        
        elif "附近" in user_input or "周边" in user_input:
            # LBS推荐（模拟位置：北京）
            nearby = nearby_recommendation(39.9, 116.4, 10.0)
            reply = "📍 附近景点推荐：\n\n"
            for spot in nearby:
                if "name" in spot:
                    reply += f"• {spot['name']} ({spot['distance']}) - {spot['description']}\n"
                else:
                    reply += spot.get("message", "未找到景点")
            self.call_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": "nearby_recommend",
                "result": len(nearby)
            })
            return reply
        
        elif "语音" in user_input or "导览词" in user_input:
            # 生成语音脚本
            # 提取景点名
            spot_name = "故宫"
            for name in SCENIC_SPOTS.keys():
                if name in user_input:
                    spot_name = name
                    break
            script = generate_audio_script(spot_name)
            self.call_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": "generate_audio",
                "result": spot_name
            })
            return script
        
        else:
            # 景点解说
            spot_name = "故宫"
            for name in SCENIC_SPOTS.keys():
                if name in user_input:
                    spot_name = name
                    break
            commentary = generate_commentary(spot_name)
            self.call_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": "generate_commentary",
                "result": spot_name
            })
            return commentary


# 全局实例
agent = GuideAgent()
