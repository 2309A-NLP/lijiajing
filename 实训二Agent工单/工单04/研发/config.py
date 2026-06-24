# -*- coding: utf-8 -*-
"""
配置模块
工单编号：人工智能NLP-Agent数字人项目-基金问答智能体任务
"""
import os

# ============================================================
# LLM 配置
# ============================================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# ============================================================
# 数据库配置
# ============================================================
DB_PATH = os.getenv("FUND_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "博金杯比赛数据.db"))

# ============================================================
# 基金数据库表结构（DDL 参考）
# ============================================================
FUND_TABLES_SCHEMA = """
【基金数据库表结构】

1. fund_basic（基金基本信息）
   - fund_code TEXT PRIMARY KEY    -- 基金代码
   - fund_name TEXT                -- 基金名称
   - fund_type TEXT                -- 基金类型
   - establish_date TEXT           -- 成立日期
   - manager TEXT                  -- 基金经理

2. fund_stock_hold（基金股票持仓明细）
   - id INTEGER PRIMARY KEY
   - fund_code TEXT                -- 基金代码
   - report_date TEXT              -- 报告期（如20210331）
   - stock_code TEXT               -- 股票代码
   - stock_name TEXT               -- 股票名称
   - hold_ratio REAL               -- 持仓占比(%)
   - hold_shares INTEGER           -- 持仓股数

3. fund_bond_hold（基金债券持仓明细）
   - id INTEGER PRIMARY KEY
   - fund_code TEXT
   - report_date TEXT
   - bond_code TEXT
   - bond_name TEXT
   - hold_ratio REAL

4. fund_convert_hold（基金可转债持仓明细）
   - id INTEGER PRIMARY KEY
   - fund_code TEXT
   - report_date TEXT
   - convert_code TEXT
   - convert_name TEXT
   - hold_ratio REAL

5. fund_daily（基金日行情表）
   - id INTEGER PRIMARY KEY
   - fund_code TEXT
   - trade_date TEXT               -- 交易日期（如20210105）
   - nav REAL                      -- 单位净值
   - accum_nav REAL                -- 累计净值
   - daily_return REAL             -- 日收益率

6. stock_a_daily（A股票日行情表）
   - id INTEGER PRIMARY KEY
   - stock_code TEXT
   - trade_date TEXT
   - open_price REAL               -- 开盘价
   - close_price REAL              -- 收盘价
   - high_price REAL               -- 最高价
   - low_price REAL                -- 最低价
   - volume BIGINT                 -- 成交量
   - amount REAL                   -- 成交额

7. stock_hk_daily（港股票日行情表）
   - id INTEGER PRIMARY KEY
   - stock_code TEXT
   - trade_date TEXT
   - close_price REAL

8. company_industry（A股公司行业划分表）
   - id INTEGER PRIMARY KEY
   - stock_code TEXT
   - trade_date TEXT
   - industry_level1 TEXT          -- 一级行业
   - industry_level2 TEXT          -- 二级行业
   - source TEXT                   -- 来源（如中信）

9. fund_scale_change（基金规模变动表）
   - id INTEGER PRIMARY KEY
   - fund_code TEXT
   - report_date TEXT
   - total_share REAL              -- 总份额
   - total_nav REAL                -- 总净值

10. fund_holder_structure（基金份额持有人结构）
    - id INTEGER PRIMARY KEY
    - fund_code TEXT
    - report_date TEXT
    - individual_ratio REAL         -- 个人持有占比
    - institutional_ratio REAL      -- 机构持有占比
"""

# ============================================================
# NL2SQL 系统提示词
# ============================================================
NL2SQL_SYSTEM = """你是一个专业的 SQL 查询生成器。给定用户的自然语言问题和基金数据库表结构，请生成正确的 SQLite 查询。

【数据库表结构】
{schema}

【规则】
1. 只输出 SQL 查询语句，不要任何解释
2. 使用 SQLite 语法
3. 日期格式：数据库中使用 TEXT 类型，格式如 '20210105'
4. 基金代码通常为6位数字
5. 百分比计算注意小数点
6. 如果问题涉及"涨跌幅"，公式为: (收盘价 - 前一日收盘价) / 前一日收盘价 * 100
7. 如果无法确定查询条件，输出: -- CANNOT_DETERMINE
8. 如果涉及多表，使用 JOIN
9. 只输出 SQL，不要 Markdown 代码块
"""

# ============================================================
# 结果总结 系统提示词
# ============================================================
SUMMARIZE_SYSTEM = """你是一个金融数据分析师。根据用户的问题和数据库查询结果，生成简洁准确的中文回答。

【要求】
1. 直接回答问题，不要多余解释
2. 数字保留合理的小数位
3. 如果结果为空，说明"未查询到相关数据"
4. 如果有多条结果，以清晰的格式列出
"""

# ============================================================
# 测试问题文件
# ============================================================
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "question.jsonl")
