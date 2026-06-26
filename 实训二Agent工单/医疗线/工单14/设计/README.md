# 工单 14：MCP (高德地图 + 自建 MCP Server)

> 工单编号：人工智能NLP-Agent数字人项目-14-MCP

## 功能概述

1. **高德地图 MCP 对接** - 医院位置相关的出行、住宿、餐饮查询
2. **自建 MCP Server** - 将已有 Tool 封装为 MCP Server，供 Agent 使用

## MCP Tools

| Tool | 描述 |
|------|------|
| `search_hospital` | 搜索指定城市的医院信息 |
| `plan_route` | 规划从起点到医院的出行路线 |
| `search_nearby` | 搜索医院周边的住宿、餐饮、药店 |
| `medical_travel_plan` | 一键生成就医出行计划 |

## 技术架构

```
用户请求 → MCP Client → MCP Server → AmapMCPClient → 高德API/模拟数据
    ↓
医疗出行计划 (医院信息 + 路线规划 + 周边配套)
```

## 快速开始

```bash
pip install -r requirements.txt
python app.py  # http://localhost:8014
```

## 验收标准

| 类别 | 要求 | 实现 |
|------|------|------|
| 功能完整性 | MCP对接医院出行/住宿/餐饮 | ✅ 4个MCP Tool |
| 自建MCP Server | 封装已有Tool为MCP | ✅ MedicalMCPServer |
