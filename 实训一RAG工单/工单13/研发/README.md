# 工单13: RAG性能瓶颈识别与优化

## 📋 工单信息
- **工单编号**: 人工智能NLP-RAG-RAG性能瓶颈识别与优化
- **创建时间**: 2025年1月（工单01-10）/ 2025年8月（工单11-13）
- **工时预估**: 1-2人日

## 📄 引用的PDF文件
招股说明书1.pdf（作为测试数据）

## ❓ 测试问题
关注检索响应时间，无特定测试问题

## 🎯 任务目标
分析RAG系统检索结果返回时间过长的原因，优化到3秒以内。

## ✅ 验收标准
用户输入query后，返回检索结果要在3秒以内

## 🏗️ 系统架构
优化分析5个阶段：
1. 查询处理与增强
2. 检索阶段
3. 上下文组装与提示工程
4. LLM生成
5. 后处理与响应格式化
工具：cProfile, snakeviz, perf, OpenTelemetry

## 📝 备注
参考：https://apxml.com/zh/courses/optimizing-rag-for-production/chapter-1-production-rag-foundations/rag-performance-bottlenecks

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
