# 工单 04：基金数据问答智能体

## 工单编号
人工智能NLP-Agent数字人项目-基金问答智能体任务

## 功能概述
基于 NL2SQL 技术的基金数据问答系统，将自然语言问题转换为 SQL 查询，从10张基金数据库表中提取数据并生成回答。

## 软件设计

### 功能清单
| 功能 | 描述 |
|------|------|
| NL2SQL | 自然语言问题 → SQL 查询语句 |
| 数据库查询 | 10张基金表的SQL执行 |
| 结果总结 | 查询结果 → 自然语言回答 |
| 批量处理 | 处理 question.jsonl 测试问题集 |

### 数据库表（10张）
| 表名 | 说明 |
|------|------|
| fund_basic | 基金基本信息 |
| fund_stock_hold | 基金股票持仓明细 |
| fund_bond_hold | 基金债券持仓明细 |
| fund_convert_hold | 基金可转债持仓明细 |
| fund_daily | 基金日行情表 |
| stock_a_daily | A股票日行情表 |
| stock_hk_daily | 港股票日行情表 |
| company_industry | A股公司行业划分表 |
| fund_scale_change | 基金规模变动表 |
| fund_holder_structure | 基金份额持有人结构 |

### NL2SQL 流程
```
用户问题 → LLM 分析意图
         ↓
    数据库 Schema 注入提示词
         ↓
    生成 SQL 查询语句
         ↓
    SQLite 执行查询
         ↓
    查询结果 → LLM 总结 → 回答
```

### 系统架构
```
┌─────────────────────────────────┐
│           app.py (CLI)          │
│   交互模式 / 批量模式            │
├──────────────┬──────────────────┤
│   agent.py   │   database.py    │
│  NL2SQL生成   │   SQLite查询     │
│  结果总结     │   Schema提取     │
├──────────────┴──────────────────┤
│           config.py             │
│   LLM配置 + NL2SQL提示词模板     │
└─────────────────────────────────┘
```

## 技术栈
- Python 3.8+
- SQLite3
- OpenAI SDK（LLM NL2SQL + 总结）
- LLM：Qwen2.5-72B-Instruct

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 下载基金数据
```bash
# 需要 git lfs
git clone https://www.modelscope.cn/datasets/BJQW14B/bs_challenge_financial_14b_dataset.git
```

### 配置环境变量
```bash
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_API_KEY="your-api-key"
export FUND_DB_PATH="/path/to/博金杯比赛数据.db"
```

### 运行
```bash
# 交互模式
python app.py

# 批量模式
python app.py --batch question.jsonl
```

## 验收标准
- 基于 question.jsonl 中的问题生成回复
- 补全 answer 字段，提交 JSONL 格式

## 文件结构
```
work_order_04/
├── app.py              # 主程序入口（交互+批量模式）
├── agent.py            # Agent核心（NL2SQL+结果总结）
├── database.py         # SQLite查询 + Schema提取
├── config.py           # 配置（LLM+NL2SQL提示词+表结构）
├── requirements.txt    # Python依赖
├── README.md           # 本文件
├── data/               # 数据目录
├── output/             # 输出目录
├── logs/               # 日志目录
└── 工单原文.txt         # PDF原文
```
