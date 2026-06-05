# 工单06: 混合检索任务

## 📋 工单信息
- **工单编号**: 人工智能NLP-RAG-混合检索任务
- **创建时间**: 2025年1月（工单01-10）/ 2025年8月（工单11-13）
- **工时预估**: 1-2人日

## 📄 引用的PDF文件
招股说明书1.pdf

## ❓ 测试问题
10个武汉兴图新科问题

## 🎯 任务目标
实现向量检索+全文检索+混合检索三种策略，支持多种检索方式的配置。

## ✅ 验收标准
1. 准确率 ≥ 90%
2. 召回率 ≥ 95%
3. 支持3种重排算法
4. 支持多种嵌入模型（bge、m3e）

## 🏗️ 系统架构
向量检索：BGE嵌入 + FAISS。
全文检索：倒排索引（Whoosh/Elasticsearch）。
混合检索：加权融合向量+全文结果。
重排：LLM重排器、TF-IDF重排器、自适应重排器。

## 📝 备注
需要安装: pip install whoosh elasticsearch（可选）。目标是让用户能选择检索策略并对比效果。

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
