# 工单01: 基于PDF文档的问答系统（基础任务）

## 📋 工单信息
- **工单编号**: 人工智能NLP-RAG-基于PDF文档的问答系统
- **创建时间**: 2025年1月（工单01-10）/ 2025年8月（工单11-13）
- **工时预估**: 1-2人日

## 📄 引用的PDF文件
招股说明书1.pdf（武汉兴图新科电子股份有限公司，548页）

## ❓ 测试问题
10个武汉兴图新科相关的问题（id: 260,95,33,34,957,793,795,543,531,207）

## 🎯 任务目标
搭建基础RAG问答系统，对比PDF检索结果 vs 纯LLM回答。

## ✅ 验收标准
1. 问答准确率 ≥ 90%
2. 响应时间 ≤ 3秒
3. 交互友好，支持中英文

## 🏗️ 系统架构
pdf_parser.py → vector_store.py → qa_engine.py → app.py
使用PyMuPDF解析PDF，BGE-small-zh生成embeddings，FAISS存储向量，Ollama(qwen2.5)生成回答。

## 📝 备注
这是基础工单，后续工单都基于此迭代。产出物包括问答界面和演示视频。

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
