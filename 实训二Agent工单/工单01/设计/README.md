# 工单 01：记账本智能体

## 工单编号
人工智能NLP-Agent数字人项目-记账本任务

## 功能概述
基于大语言模型的家庭记账本智能体，支持自然语言交互，实现家庭成员（爸爸、妈妈、女儿）的收入/支出记录、查询、删除等功能。

## 软件设计

### 功能清单
| 功能 | 描述 |
|------|------|
| 记账 | 从自然语言中提取日期、人物、事项、金额并存储 |
| 查询 | 按成员/日期/类别查询记账记录，支持汇总统计 |
| 删除 | 删除指定记录，需用户确认 |
| 引导 | 对不完整输入进行引导补充 |

### 数据库设计
**表名：** `money_notes`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| member | TEXT NOT NULL | 家庭成员（爸爸/妈妈/女儿） |
| date | TEXT NOT NULL | 日期（YYYY-MM-DD） |
| category | TEXT NOT NULL | 类别（购物/餐饮/交通等） |
| item | TEXT NOT NULL | 具体事项描述 |
| amount | REAL NOT NULL | 金额（正数收入，负数支出） |
| type | TEXT NOT NULL | 类型（收入/支出） |
| created_at | TEXT | 创建时间 |

### 流程图
```
用户输入 → LLM 解析 JSON
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
  record      query      delete
    ↓           ↓           ↓
 写入SQLite  查询+汇总   确认→删除
    ↓           ↓           ↓
  回复用户    回复明细    回复结果
```

### 系统架构
```
┌─────────────────────────────────┐
│           app.py (CLI)          │
│    用户交互 → 调度 → 回复        │
├──────────────┬──────────────────┤
│   agent.py   │   database.py    │
│  LLM解析意图  │   SQLite操作     │
│  生成回复     │   CRUD + 统计    │
├──────────────┴──────────────────┤
│           config.py             │
│     LLM配置 + 系统提示词         │
└─────────────────────────────────┘
```

## 技术栈
- Python 3.8+
- SQLite3（内置）
- OpenAI SDK（LLM API 调用）
- LLM：Qwen2.5-72B-Instruct（可配置）

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="Qwen/Qwen2.5-72B-Instruct"
```

### 运行
```bash
python app.py
```

## 测试用例

### 验收标准测试
| 测试语句 | 预期行为 |
|----------|----------|
| 今天女儿买了双登山鞋499元 | 记录支出499元 |
| 7月5日妈妈收到报销1000元 | 记录收入1000元 |
| 看下这个月家里花钱明细 | 查询本月支出汇总 |
| 这个月女儿花了多少钱？ | 查询女儿本月支出 |
| 删除女儿报旅游团的费用 | 确认删除→执行删除 |

### 数据库调用率
- 所有记账操作100%调用数据库存储
- 所有查询操作100%从数据库读取

## 文件结构
```
work_order_01/
├── app.py              # 主程序入口
├── agent.py            # Agent核心（LLM解析+回复生成）
├── config.py           # 配置（LLM/数据库/提示词）
├── database.py         # SQLite数据库操作
├── requirements.txt    # Python依赖
├── README.md           # 本文件
├── data/               # 数据库文件目录
│   └── money_notes.db
└── logs/               # 日志目录
```
