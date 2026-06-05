# 工单11: Embeddings模型微调

## 📋 工单信息
- **工单编号**: 人工智能NLP-RAG-Embeddings模型微调
- **创建时间**: 2025年1月（工单01-10）/ 2025年8月（工单11-13）
- **工时预估**: 1-2人日

## 📄 引用的PDF文件
招股说明书1.pdf（作为微调数据来源）

## ❓ 测试问题
微调前后对比评估

## 🎯 任务目标
在专业领域数据上微调BAAI/bge-base-en-v1.5嵌入模型，弥补语义鸿沟。

## ✅ 验收标准
1. 微调后的模型检索效果比微调前好
2. 有数据指标支撑对比

## 🏗️ 系统架构
基座模型：BAAI/bge-base-en-v1.5
损失函数：Triplet Loss / Contrastive Loss / Cosine Similarity Loss
调库：sentence-transformers

## 📝 备注
参考：https://zhuanlan.zhihu.com/p/1918237424745714815
使用pip install sentence-transformers[dev]

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
