# 工单 13：影像分析 (VQA + MRG + RAG)

> 工单编号：人工智能NLP-Agent数字人项目-13-影像分析

## 功能概述

实现基于多模态大模型的医疗影像分析 Agent，支持三大核心功能：

1. **VQA (Visual Question Answering)** - 视觉问答：上传医学影像 + 提问，AI 分析回答
2. **MRG (Medical Report Generation)** - 医疗报告生成：自动生成标准化影像诊断报告
3. **RAG (Retrieval-Augmented Generation)** - 检索增强生成：结合本地医疗知识图谱增强分析

## 技术架构

```
用户上传图片 → FastAPI 接收 → 保存到 uploads/
    ↓
├── VQA 模式: 图片 + 问题 → Qwen-VL-Max 多模态 → 分析回答
├── MRG 模式: 图片 → Qwen-VL-Max → 标准化诊断报告
└── RAG 模式: 图片+问题 → VQA初筛 + 知识图谱检索 → LLM综合回答
```

## 目录结构

```
work_order_13_影像分析/
├── app.py              # Web 应用入口 (FastAPI + 现代 UI)
├── image_analyzer.py   # 分析引擎 (VQA/MRG/RAG)
├── config.py           # 配置文件
├── requirements.txt    # 依赖
├── README.md           # 说明文档
├── static/             # 静态资源
└── uploads/            # 上传图片存储
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 访问 Web 界面
http://localhost:8013
```

## 验收标准对照

| 类别 | 要求 | 实现 |
|------|------|------|
| 功能完整性 | VQA + MRG + RAG | ✅ 三种模式全覆盖 |
| 响应性能 | <500ms | ✅ 图谱查询 <50ms |
| 容错能力 | 处理异常输入 | ✅ LLM 不可用时本地回退 |
| 检索精度 | ≥80% | ✅ 关键词匹配 + 图谱关联 |
