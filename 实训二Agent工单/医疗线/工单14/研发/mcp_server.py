# -*- coding: utf-8 -*-
"""
work_order_14 MCP - 自建 MCP Server
将已完成的 Tool (医院搜索、路线规划、周边查询) 封装为 MCP Server
工单编号：人工智能NLP-Agent数字人项目-14-MCP
"""
import json
from amap_mcp import AmapMCPClient


# ============================================================
# MCP Tool 定义 (符合 MCP 规范)
# ============================================================
MCP_TOOLS = [
    {
        "name": "search_hospital",
        "description": "搜索指定城市的医院信息，包括名称、地址、电话等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如北京、上海"},
                "keyword": {"type": "string", "description": "搜索关键词，如医院、诊所、药店"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "plan_route",
        "description": "规划从起点到医院的出行路线",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "起点坐标 (经纬度，逗号分隔)"},
                "destination": {"type": "string", "description": "终点坐标 (经纬度，逗号分隔)"},
                "mode": {"type": "string", "enum": ["driving", "walking", "transit"], "description": "出行方式"}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "search_nearby",
        "description": "搜索医院周边的住宿、餐饮、药店等设施",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "中心点坐标"},
                "category": {"type": "string", "enum": ["餐饮", "住宿", "药店", "停车场"], "description": "设施类型"},
                "radius": {"type": "integer", "description": "搜索半径（米）"}
            },
            "required": ["location", "category"]
        }
    },
    {
        "name": "medical_travel_plan",
        "description": "一键生成就医出行计划（医院信息 + 路线 + 周边配套）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市"},
                "hospital_name": {"type": "string", "description": "医院名称关键词"},
                "need_route": {"type": "boolean", "description": "是否需要路线规划"},
                "need_nearby": {"type": "boolean", "description": "是否需要周边配套"}
            },
            "required": ["city"]
        }
    }
]


class MedicalMCPServer:
    """自建医疗 MCP Server"""
    
    def __init__(self):
        self.client = AmapMCPClient()
        self.tools = {t["name"]: t for t in MCP_TOOLS}
    
    def list_tools(self) -> list:
        """列出所有可用的 MCP Tools"""
        return MCP_TOOLS
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """调用指定的 MCP Tool"""
        if tool_name == "search_hospital":
            return self.client.search_hospitals(
                city=arguments.get("city", "北京"),
                keyword=arguments.get("keyword", "医院")
            )
        
        elif tool_name == "plan_route":
            return self.client.plan_route(
                origin=arguments.get("origin", "116.3974,39.9093"),
                destination=arguments.get("destination", "116.4183,39.9146"),
                mode=arguments.get("mode", "driving")
            )
        
        elif tool_name == "search_nearby":
            return self.client.search_nearby(
                location=arguments.get("location", "116.4183,39.9146"),
                category=arguments.get("category", "餐饮"),
                radius=arguments.get("radius", 1000)
            )
        
        elif tool_name == "medical_travel_plan":
            return self._full_travel_plan(
                city=arguments.get("city", "北京"),
                hospital_name=arguments.get("hospital_name", ""),
                need_route=arguments.get("need_route", True),
                need_nearby=arguments.get("need_nearby", True)
            )
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _full_travel_plan(self, city, hospital_name, need_route, need_nearby) -> dict:
        """完整就医出行计划"""
        # 1. 搜索医院
        hospitals = self.client.search_hospitals(city, hospital_name or "医院")
        if not hospitals:
            return {"error": "未找到匹配的医院"}
        
        plan = {"hospital": hospitals[0], "steps": []}
        hospital_loc = hospitals[0].get("location", "")
        
        # 2. 路线规划
        if need_route and hospital_loc:
            route = self.client.plan_route("116.3974,39.9093", hospital_loc, "driving")
            plan["route"] = route
            plan["steps"].append("🚗 已规划出行路线")
        
        # 3. 周边配套
        if need_nearby and hospital_loc:
            dining = self.client.search_nearby(hospital_loc, "餐饮")
            hotel = self.client.search_nearby(hospital_loc, "住宿")
            plan["nearby"] = {"餐饮": dining, "住宿": hotel}
            plan["steps"].append("🏨 已查询周边餐饮和住宿")
        
        plan["steps"].append("✅ 就医出行计划生成完成")
        return plan


def demo_test():
    print("="*60)
    print("🧪 工单 14 MCP - 自建 MCP Server 测试")
    print("="*60)
    
    server = MedicalMCPServer()
    
    print("\n--- 列出可用 Tools ---")
    for tool in server.list_tools():
        print(f"  📦 {tool['name']}: {tool['description']}")
    
    print("\n--- 调用 search_hospital ---")
    result = server.call_tool("search_hospital", {"city": "北京", "keyword": "协和"})
    print(f"  结果: {len(result)} 条")
    if result and "name" in result[0]:
        print(f"  🏥 {result[0]['name']}")
    
    print("\n--- 调用 medical_travel_plan ---")
    plan = server.call_tool("medical_travel_plan", {
        "city": "北京",
        "hospital_name": "协和",
        "need_route": True,
        "need_nearby": True
    })
    if "hospital" in plan:
        print(f"  🏥 目标: {plan['hospital']['name']}")
        print(f"  📋 步骤: {', '.join(plan['steps'])}")
    
    print("\n✅ MCP Server 测试完成")


if __name__ == "__main__":
    demo_test()
