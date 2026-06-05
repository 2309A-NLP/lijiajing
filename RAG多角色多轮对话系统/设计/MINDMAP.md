# DeepRole v9.0 思维导图

## 一、DeepRole v9.0

### 1.1 前端层
#### 1.1.1 页面
- login.html（登录注册）
- splash.html（人格测试）
- chat.html（主对话）
- dashboard.html（数据统计）
- share.html（分享链接）

#### 1.1.2 功能
- 5种角色切换（虚拟朋友/心理医生/律师/分析师/奶茶师）
- 3种人格切换（默认/暴躁老哥/知性姐姐）
- 流式对话显示
- 收藏/金句墙/成就系统
- 深色模式/氛围特效

### 1.2 后端层（FastAPI）

#### 1.2.1 查询优化
- 查询改写（DeepSeek优化检索语句）
- 查询扩写（多角度生成）
- 提示词增强（角色×人格专属）

#### 1.2.2 多路召回
- Milvus（向量语义检索）
- BM25（关键词检索）
- MySQL（历史对话检索）
- Redis（缓存检索）
- Neo4j（知识图谱推理）
- 互联网（DuckDuckGo搜索）

#### 1.2.3 融合排序
- RRF算法（Reciprocal Rank Fusion）
- 权重配置（Milvus 0.5 / BM25 0.3 / 其他 0.2）
- 去重合并

#### 1.2.4 重排序
- BGE-Reranker-v2-m3
- 余弦相似度过滤（≥0.6）

#### 1.2.5 生成
- DeepSeek API
- 流式输出（SSE协议）

#### 1.2.6 后处理
- 安全校验
- 敏感词过滤
- 角色一致性检查

### 1.3 数据层

#### 1.3.1 向量数据库
- Milvus（知识库向量存储）
- BGE-M3（1024维向量）

#### 1.3.2 关系数据库
- MySQL（用户/收藏/分享/历史）

#### 1.3.3 缓存
- Redis（对话历史/检索缓存）

#### 1.3.4 文件存储
- knowledge_docs/（原始文档）

### 1.4 部署层

#### 1.4.1 容器
- milvus-standalone
- milvus-minio
- milvus-etcd

#### 1.4.2 启动
- start.bat（一键启动）
- venv（虚拟环境）

---

## 二、文件结构
D:\rag_roleplay_system/
├── app/ # 主程序模块
│ ├── main.py # FastAPI主程序
│ └── README.md
├── retrieval/ # 检索召回模块
│ ├── milvus_search.py # Milvus向量检索
│ ├── hybrid_search.py # MySQL检索
│ ├── bm25_search.py # BM25检索
│ ├── cache_search.py # Redis缓存
│ ├── multi_recall.py # 多路召回融合
│ ├── rewrite_query.py # 查询改写
│ ├── query_expand.py # 查询扩写
│ ├── web_search.py # 互联网搜索
│ └── README.md
├── validation/ # 后处理模块
│ ├── post_check.py # 安全校验
│ └── README.md
├── utils/ # 辅助工具
│ ├── import_knowledge.py # 知识库导入
│ ├── build_bm25_index.py # BM25索引构建
│ ├── check_kb.py # 知识库检查
│ ├── fix_milktea.py # 奶茶知识导入
│ ├── summary_history.py # 对话摘要
│ └── README.md
├── data/knowledge_docs/ # 知识文档
├── templates/ # 前端页面
├── venv/ # 虚拟环境
├── start.bat # 一键启动
└── README.md # 项目说明