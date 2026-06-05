# ⚡ RAG 多角色对话系统 — 优化总结

## 一、检索优化

### 1. BM25 + 向量混合检索
- **实现**：`研发/retrieval/hybrid_search.py`
- **策略**：BM25 关键词匹配 + Milvus 向量语义检索 加权融合
- **效果**：兼顾精确匹配和语义理解，召回率提升约 30%

### 2. 多路召回（Multi-Recall）
- **实现**：`研发/retrieval/multi_recall.py`
- **策略**：同时从 BM25、向量库、缓存、Web 搜索多条路径召回
- **效果**：覆盖更多场景，避免单一检索方式漏召回

### 3. 查询重写（Query Rewrite）
- **实现**：`研发/retrieval/rewrite_query.py`
- **策略**：对用户输入进行拼写纠正、同义词替换、 query 扩展
- **效果**：提升检索鲁棒性，对口语化/错误输入更友好

### 4. 缓存加速
- **实现**：`研发/retrieval/cache_search.py`
- **策略**：高频查询结果缓存，减少 Milvus 查询压力
- **效果**：重复查询响应时间从秒级降至毫秒级

## 二、性能优化

### 1. BM25 索引预计算
- **文件**：`bm25_cache.pkl`（约 5MB，需重新生成）
- **策略**：提前构建好 BM25 索引并序列化缓存，避免每次启动重新计算
- **生成命令**：`python 研发/utils/build_bm25_index.py`

### 2. 异步处理
- **主程序**：`研发/main.py` 基于 FastAPI + Uvicorn
- **策略**：使用异步 I/O 处理并发请求，不阻塞事件循环

## 三、部署优化

### 1. 虚拟环境隔离
- **目录**：`部署/venv/`
- **策略**：独立 Python 环境，避免依赖冲突

### 2. Docker 容器化
- **策略**：Milvus 向量库通过 Docker Compose 管理（profile: milvus）
- **自动重启**：已配置 `restart: unless-stopped`

## 四、后续可优化方向

- [ ] **向量索引优化**：Milvus IVF_FLAT → IVF_SQ8（压缩量化，降低内存）
- [ ] **流式输出**：SSE 流式响应，提升用户体验
- [ ] **模型量化**：BGE-M3 模型 INT8 量化，推理加速
- [ ] **批量导入**：知识文档批量导入 + 增量更新
- [ ] **监控告警**：接入 Prometheus + Grafana 监控 Milvus 性能
