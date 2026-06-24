# 工单 03：文生图智能体

## 工单编号
人工智能NLP-Agent数字人项目-文生图智能体任务

## 功能概述
基于大语言模型的图像生成智能体，支持面部多角度生成（正面/左转/右转）、图像扩图、文生图等功能。NLP方向重点在于LLM提示词优化与生成调度。

## 软件设计

### 功能清单
| 功能 | 描述 |
|------|------|
| 面部多角度生成 | 给定面部描述，生成正面/左转30°/右转30°/扩图共4张 |
| 文生图 | 文字描述直接生成图片 |
| 图像扩图 | 扩展图像背景环境 |
| 提示词优化 | LLM自动优化用户描述为专业级英文提示词 |

### 系统架构
```
┌─────────────────────────────────┐
│           app.py (CLI)          │
│    用户交互 → 意图分析 → 调度    │
├──────────────┬──────────────────┤
│   agent.py   │   image_api.py   │
│  意图识别     │   图像生成API     │
│  提示词优化   │   多后端支持      │
│  结果格式化   │   图片保存        │
├──────────────┴──────────────────┤
│           config.py             │
│   LLM + 图像API + 提示词模板     │
└─────────────────────────────────┘
```

### 提示词优化流程
```
用户描述（中文）→ LLM 分析面部特征
                ↓
    生成4个视角的英文提示词：
    ├─ straight（正面）
    ├─ turn_left（左转30°）
    ├─ turn_right（右转30°）
    └─ outpainting（扩图）
                ↓
    调用图像生成API → 保存图片到 output/
```

### 支持的图像后端
| 后端 | 环境变量 | 模型 |
|------|---------|------|
| SiliconFlow | IMAGE_API_TYPE=siliconflow | FLUX.1-schnell |
| OpenAI DALL-E 3 | IMAGE_API_TYPE=openai | dall-e-3 |
| 本地 SD WebUI | IMAGE_API_TYPE=local_sd | 本地模型 |
| 模拟模式 | IMAGE_API_TYPE=mock | 占位文件 |

## 技术栈
- Python 3.8+
- OpenAI SDK（LLM + 图像API）
- requests（本地SD调用）
- LLM：Qwen2.5-72B-Instruct

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
# LLM 配置
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_API_KEY="your-api-key"

# 图像 API 配置（可选，默认使用 LLM 配置）
export IMAGE_API_TYPE="siliconflow"
export IMAGE_API_KEY="your-image-api-key"
```

### 运行
```bash
python app.py
```

## 验收标准

### 功能层面
- 输入面部描述，生成3张多角度效果图 + 扩图

### 效果层面
| 指标 | 要求 |
|------|------|
| 面部特征保持 | 五官形状、眼睛颜色、肤色一致 |
| 角度准确性 | 左右偏转±30°以内 |
| 图像清晰度 | 高清晰度，无模糊/失真 |
| 扩图一致性 | 扩图部分与原始内容一致，无拼接痕迹 |

## 文件结构
```
work_order_03/
├── app.py              # 主程序入口
├── agent.py            # Agent核心（意图识别+提示词优化）
├── image_api.py        # 图像生成API封装
├── config.py           # 配置（LLM/图像API/提示词模板）
├── requirements.txt    # Python依赖
├── README.md           # 本文件
├── data/               # 数据目录
├── output/             # 生成的图片输出目录
├── logs/               # 日志目录
└── 工单原文.txt         # PDF原文
```
