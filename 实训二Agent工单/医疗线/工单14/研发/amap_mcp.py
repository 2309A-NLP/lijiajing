# -*- coding: utf-8 -*-
"""
work_order_14 MCP - 高德地图 MCP 对接模块
工单编号：人工智能NLP-Agent数字人项目-14-MCP
功能: 对接高德地图 MCP，实现医院位置相关的出行、住宿、餐饮查询
"""
import json
import requests
from config import AMAP_API_KEY, AMAP_BASE_URL, DEFAULT_CITY


class AmapMCPClient:
    """高德地图 MCP 客户端"""
    
    def __init__(self, api_key=AMAP_API_KEY):
        self.api_key = api_key
        self.base_url = AMAP_BASE_URL
        self.has_real_key = bool(api_key) and api_key != ""
    
    # ============================================================
    # 1. POI 搜索 (医院、药店等)
    # ============================================================
    def search_hospitals(self, city: str = DEFAULT_CITY, keyword: str = "医院", limit: int = 10) -> list:
        """
        搜索医院 (MCP Tool: poi_search)
        高德 API: /place/text
        """
        if self.has_real_key:
            return self._real_search("hospital", city, keyword, limit)
        return self._simulate_hospitals(city, keyword, limit)
    
    def _real_search(self, poitype, city, keyword, limit):
        """真实高德 API 调用"""
        url = f"{self.base_url}/place/text"
        params = {
            "key": self.api_key,
            "keywords": keyword,
            "city": city,
            "citylimit": "true",
            "types": poitype,
            "offset": limit,
            "page": 1,
            "extensions": "all"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "1":
                return [{
                    "name": p["name"],
                    "address": p.get("address", ""),
                    "location": p.get("location", ""),
                    "tel": p.get("tel", ""),
                    "type": p.get("type", "")
                } for p in data.get("pois", [])[:limit]]
        return []
    
    def _simulate_hospitals(self, city, keyword, limit):
        """模拟数据 (无 API Key 时)"""
        hospitals = {
            "北京": [
                {"name": "北京协和医院", "address": "北京市东城区帅府园1号", "location": "116.4183,39.9146", "tel": "010-69156114", "type": "三级甲等"},
                {"name": "北京大学第一医院", "address": "北京市西城区西什库大街8号", "location": "116.3732,39.9275", "tel": "010-83572211", "type": "三级甲等"},
                {"name": "北京同仁医院", "address": "北京市东城区东交民巷1号", "location": "116.4208,39.9034", "tel": "010-58266699", "type": "三级甲等"},
                {"name": "北京301医院", "address": "北京市海淀区复兴路28号", "location": "116.2884,39.9048", "tel": "010-66936114", "type": "三级甲等"},
                {"name": "北京儿童医院", "address": "北京市西城区南礼士路56号", "location": "116.3604,39.9176", "tel": "010-59612345", "type": "三级甲等"},
            ],
            "上海": [
                {"name": "上海瑞金医院", "address": "上海市黄浦区瑞金二路197号", "location": "121.4692,31.2135", "tel": "021-64370045", "type": "三级甲等"},
                {"name": "上海中山医院", "address": "上海市徐汇区枫林路180号", "location": "121.4576,31.2012", "tel": "021-64041990", "type": "三级甲等"},
            ]
        }
        return hospitals.get(city, hospitals["北京"])[:limit]
    
    # ============================================================
    # 2. 出行路线规划 (MCP Tool: route_planning)
    # ============================================================
    def plan_route(self, origin: str, destination: str, mode: str = "driving") -> dict:
        """
        出行路线规划 (MCP Tool: route_planning)
        mode: driving(驾车), walking(步行), transit(公交)
        """
        if self.has_real_key:
            return self._real_route(origin, destination, mode)
        return self._simulate_route(origin, destination, mode)
    
    def _real_route(self, origin, destination, mode):
        url = f"{self.base_url}/direction/{mode}"
        params = {"key": self.api_key, "origin": origin, "destination": destination}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "1":
                route = data["route"]["paths"][0]
                return {
                    "distance": f"{int(route['distance'])/1000:.1f}km",
                    "duration": f"{int(route['duration'])//60}分钟",
                    "steps": len(route.get("steps", []))
                }
        return {"error": "路线规划失败"}
    
    def _simulate_route(self, origin, destination, mode):
        import random
        distances = {"driving": (5.2, "驾车"), "walking": (2.1, "步行"), "transit": (6.8, "公交")}
        dist, label = distances.get(mode, distances["driving"])
        return {
            "distance": f"{dist + random.uniform(-1, 1):.1f}km",
            "duration": f"{int(dist * 4 + random.randint(-2, 2))}分钟",
            "mode": label,
            "steps": [
                {"instruction": f"从起点出发，沿主路{label}", "distance": f"{dist/3:.1f}km"},
                {"instruction": "转入医院方向道路", "distance": f"{dist/3:.1f}km"},
                {"instruction": "到达目的地", "distance": f"{dist/3:.1f}km"}
            ]
        }
    
    # ============================================================
    # 3. 周边搜索 (住宿、餐饮) (MCP Tool: nearby_search)
    # ============================================================
    def search_nearby(self, location: str, category: str = "餐饮", radius: int = 1000, limit: int = 5) -> list:
        """
        搜索周边设施 (MCP Tool: nearby_search)
        category: 餐饮, 住宿, 药店, 停车场
        """
        if self.has_real_key:
            return self._real_nearby(location, category, radius, limit)
        return self._simulate_nearby(location, category, limit)
    
    def _real_nearby(self, location, category, radius, limit):
        category_map = {"餐饮": "050000", "住宿": "060000", "药店": "090101", "停车场": "150904"}
        url = f"{self.base_url}/place/around"
        params = {
            "key": self.api_key,
            "location": location,
            "types": category_map.get(category, ""),
            "radius": radius,
            "offset": limit
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "1":
                return [{"name": p["name"], "address": p.get("address", "")} for p in data.get("pois", [])[:limit]]
        return []
    
    def _simulate_nearby(self, location, category, limit):
        nearby_data = {
            "餐饮": [
                {"name": "和府捞面", "address": "医院正门向东50米", "rating": "4.5"},
                {"name": "沙县小吃", "address": "医院南门对面", "rating": "4.2"},
                {"name": "瑞幸咖啡", "address": "医院门诊大厅一楼", "rating": "4.7"},
                {"name": "全家便利店", "address": "医院住院部B1层", "rating": "4.3"},
            ],
            "住宿": [
                {"name": "如家酒店(医院店)", "address": "距医院步行3分钟", "price": "¥189/晚"},
                {"name": "汉庭酒店", "address": "距医院步行8分钟", "price": "¥159/晚"},
                {"name": "全季酒店", "address": "距医院步行12分钟", "price": "¥269/晚"},
            ],
            "药店": [
                {"name": "同仁堂药店", "address": "医院门口", "hours": "24小时"},
                {"name": "海王星辰", "address": "医院对面商业街", "hours": "08:00-22:00"},
            ]
        }
        return nearby_data.get(category, nearby_data["餐饮"])[:limit]
    
    # ============================================================
    # 4. 地理编码 (地址转坐标) (MCP Tool: geocode)
    # ============================================================
    def geocode(self, address: str) -> dict:
        """地址转坐标"""
        if self.has_real_key:
            url = f"{self.base_url}/geocode/geo"
            resp = requests.get(url, params={"key": self.api_key, "address": address}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1" and data.get("geocodes"):
                    loc = data["geocodes"][0]["location"]
                    return {"address": address, "location": loc}
        return {"address": address, "location": "116.3974,39.9093", "note": "模拟坐标 (北京)"}


def demo_test():
    print("="*60)
    print("🧪 工单 14 MCP - 高德地图对接测试")
    print("="*60)
    
    client = AmapMCPClient()
    
    print("\n--- 测试 1: 搜索医院 ---")
    hospitals = client.search_hospitals("北京", "医院")
    print(f"找到 {len(hospitals)} 家医院")
    for h in hospitals[:3]:
        print(f"  🏥 {h['name']} - {h['address']}")
    
    print("\n--- 测试 2: 出行路线 ---")
    route = client.plan_route("116.3974,39.9093", "116.4183,39.9146", "driving")
    print(f"  距离: {route['distance']}, 时间: {route['duration']}")
    
    print("\n--- 测试 3: 周边餐饮 ---")
    nearby = client.search_nearby("116.4183,39.9146", "餐饮")
    for n in nearby[:3]:
        print(f"  🍽️ {n['name']} - {n['address']}")
    
    print("\n✅ 工单 14 MCP 测试完成")


if __name__ == "__main__":
    demo_test()
