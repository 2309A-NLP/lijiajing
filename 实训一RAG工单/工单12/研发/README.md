# 工单12: LightRAG优化

## 📋 工单信息
- **工单编号**: 人工智能NLP-RAG-LightRAG优化
- **创建时间**: 2025年1月（工单01-10）/ 2025年8月（工单11-13）
- **工时预估**: 1-2人日

## 📄 引用的PDF文件
招股说明书1.pdf + 招股说明书2.pdf

## ❓ 测试问题
16个问题（id: 5,6,1,2,3,4,260,95,33,34,957,793,795,543,531,207）

## 🎯 任务目标
使用LightRAG构建知识图谱，对比RAG vs LightRAG的检索效果。

## ✅ 验收标准
1. 根据PDF内容优化图谱实体和关系
2. 对16个问题给出RAG vs LightRAG对比
3. RAGAS指标对比

## 🏗️ 系统架构
LightRAG：github.com/HKUDS/LightRAG
轻量级RAG+图结构+增量更新+双层检索。
支持切换RAG或LightRAG知识库。

## 📝 备注
安装：pip install lightrag-hku
LightRAG内置图存储能力，不需要额外Neo4j。

---

> ⚠️ **独立性说明**: 本工单独立运行，所有代码和配置均在本目录下，不依赖其他工单。
> 
> **运行方式**:
> 1. `python pdf_parser.py` — 解析PDF，生成chunks
> 2. `python vector_store.py` — 构建向量库（FAISS）
> 3. `python qa_engine.py` — 启动问答引擎
> 4. `python app.py` — 启动Web界面
>
> **环境配置**: Python 3.12, 需要安装 PyMuPDF, sentence-transformers, faiss-cpu, langchain-ollama
