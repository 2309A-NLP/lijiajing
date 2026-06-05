# 工单1：基于PDF文档的问答系统

基于 RAG（检索增强生成）技术，构建能够解析 PDF 文档并进行智能问答的基础系统。

## 目录结构

| 文件夹 | 内容 |
|--------|------|
| 设计/ | 系统架构思维导图 |
| 研发/ | 核心代码（PDF解析、向量存储、问答引擎） |
| 测试/ | 功能测试截图 |
| 优化/ | 优化点总结 |
| 部署/ | 部署脚本与说明 |

## 技术栈

- PDF解析：PyMuPDF / pdfplumber
- 向量数据库：Milvus
- Embedding：BGE-small-zh-v1.5
- LLM：Qwen2.5 (Ollama) / DeepSeek API
