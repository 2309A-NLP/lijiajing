<p align="center">
  <img src="https://img.shields.io/badge/2309A--NLP-RAG%20%E5%A4%9A%E8%A7%92%E8%89%B2%E5%AF%B9%E8%AF%9D%E7%B3%BB%E7%BB%9F-8B5CF6?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/%E7%8A%B6%E6%80%81-%E8%BF%90%E8%A1%8C%E4%B8%AD-success?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/%E6%8A%80%E6%9C%AF%E6%A0%88-FastAPI%20%7C%20Milvus%20%7C%20DeepSeek-6366f1?style=for-the-badge"/>
</p>

<h1 align="center">🎭 RAG 多角色对话系统</h1>
<h3 align="center">基于 RAG 技术的 AI 角色扮演 · 多路召回 · 流式对话</h3>

---

## 📖 项目简介

> **一个基于 RAG（检索增强生成）的多角色 AI 对话系统**  
> 支持多角色扮演、知识库检索、多路召回、流式输出

### 核心能力

| 能力 | 技术实现 |
|------|----------|
| 🎭 **多角色扮演** | DeepSeek API + 角色提示词模板 |
| 🔍 **RAG 检索增强** | BM25 + Milvus 向量检索 + 混合搜索 |
| 🛣️ **多路召回** | 4 路并行检索 + RRF 融合排序 |
| ✏️ **查询重写** | DeepSeek 优化检索语句 |
| 📚 **知识库管理** | PDF/TXT 文档导入 → 向量化存储 |
| ⚡ **流式输出** | Server-Sent Events 实时生成 |

---

## 📂 项目结构

```
├── 设计/          # 架构文档、思维导图、项目大纲
├── 研发/          # 核心代码
│   ├── main.py          # 主程序入口
│   ├── retrieval/       # 检索模块（BM25/向量/混合）
│   ├── utils/           # 工具函数
│   ├── validation/      # 结果验证
│   ├── templates/       # 前端页面
│   ├── knowledge_docs/  # 知识文档
│   └── data/            # 数据文件
├── 测试/          # 测试截图
├── 优化/          # 优化总结
└── 部署/          # 依赖清单、启动说明
```

---

## 🚀 快速开始

### 前置条件

- Python 3.10+
- Docker Desktop（运行 Milvus 向量库）
- DeepSeek API Key

### 安装

```bash
# 1. 安装依赖
pip install -r 部署/requirements.txt

# 2. 启动 Milvus
cd /d/dify-main/docker
docker compose --profile milvus up -d

# 3. 导入知识文档
python 研发/utils/import_knowledge.py

# 4. 启动系统
python 研发/main.py

# 5. 打开浏览器访问
# http://localhost:8000
```

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **Milvus** | 向量数据库 |
| **BM25** | 关键词检索 |
| **DeepSeek** | 对话生成 |
| **BGE-Reranker** | 重排序 |
| **Redis** | 会话缓存 |
| **MySQL** | 持久化存储 |

---

## 📸 运行截图

| 对话界面 | 数据管理 | 检索测试 |
|---------|---------|---------|
| ![chat](测试/screenshots/06_Browser_Chat.png) | ![attu](测试/screenshots/01_Attu_Schema.png) | ![postman](测试/screenshots/05_Postman.png) |

---

## 👤 作者

**李佳晶** — 2309A 班

[GitHub](https://github.com/lijiajing-11)
