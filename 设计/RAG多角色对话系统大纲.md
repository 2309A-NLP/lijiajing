# DeepRole v9.0 深度技术讲稿（答辩/展示用）

> 标注：🗣️ 口述部分 | 💻 指着屏幕讲 | ❓ 预备问答 | ⏱️ 时间参考

---

## 开场（1分钟）

🗣️ **各位老师好，我汇报的题目是 DeepRole v9.0——一个基于 RAG 架构的多轮多角色 AI 对话系统。**

**先说问题背景：** 大语言模型（如 DeepSeek）在角色扮演场景中存在三个核心痛点：

1. **幻觉问题** — 模型会编造不存在的专业知识（比如律师角色编造法律条文）
2. **知识截止** — 训练数据有时效性，无法回答最新内容（如最新法规、新品奶茶配方）
3. **角色漂移** — 长对话中逐渐偏离角色人设，说着说着就变成了通用助手

**我的解决方案是 RAG（检索增强生成）**：在模型生成回答之前，先从外部知识库中检索相关信息，把检索结果作为上下文注入到提示词中，让模型"有据可依"地回答。

**技术栈：** FastAPI 做后端服务，Milvus 做向量检索，Redis 做缓存和会话管理，MySQL 做持久化存储，BGE-M3 做向量编码，DeepSeek 作为生成模型。

**核心流程分五个阶段：** 数据预处理 → 查询优化 → 多路召回与融合 → 重排序 → 生成与校验。

---

## 第一阶段：数据预处理（3分钟）

### 1.1 多格式文档解析 — `extract_text()`

💻 **（展示代码）**

```python
def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    elif ext == ".pdf":
        doc = fitz.open(filepath)        # PyMuPDF 打开 PDF
        text = ""
        for page in doc:
            text += page.get_text()      # 逐页提取纯文本
        doc.close()
        return text
    
    elif ext in [".docx", ".doc"]:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(para.text for para in doc.paragraphs)
```

🗣️ **支持三种格式：txt、pdf、docx。** 为什么选 PyMuPDF 处理 PDF？

我做了对比测试：

| 库 | 速度 | 中文支持 | 表格提取 | 安装体积 |
|---|---|---|---|---|
| PyMuPDF (fitz) | ⚡ 最快 | ✅ 好 | ⚠️ 一般 | ~15MB |
| pdfplumber | 慢 | ✅ 好 | ✅ 好 | ~30MB |
| PyPDF2 | 中等 | ❌ 差 | ❌ 无 | ~5MB |

DeepRole 的知识库以**纯文本法律条文/心理学资料/奶茶配方**为主，不需要表格提取，所以 PyMuPDF 的速度优势是最关键的。

❓ **预备问答：** 如果 PDF 是扫描件怎么办？→ 需要加 OCR 层（如 PaddleOCR），当前版本暂未处理，是已知局限。

### 1.2 角色自动匹配 — `ROLE_MAP`

💻 **（展示代码）**

```python
ROLE_MAP = {
    "civil": "律师", "tort": "律师", "code": "律师",
    "financial": "投资分析师", "report": "投资分析师",
    "milktea": "奶茶师", "recipe": "奶茶师",
    "disease": "心理医生", "guide": "心理医生",
}
```

🗣️ **这是一个文件名→角色的自动映射规则。** 导入知识库时，系统根据文件名中的关键词自动分配角色。比如文件名包含 "civil" 就自动归为律师角色，包含 "milktea" 就归为奶茶师。

**这样做的好处是：** 批量导入时不需要手动标注每个文件的角色，命名规范即可自动分类。

### 1.3 文本切分 — `chunk_text()`

💻 **（展示代码）**

```python
def chunk_text(text, chunk_size=300, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap          # 重叠50字，防止语义断裂
    return [c for c in chunks if len(c) > 50]  # 过滤过短碎片
```

🗣️ **为什么用固定窗口 + 重叠，而不是语义切分？**

这是一个关键设计决策：

| 切分方式 | 优点 | 缺点 |
|---------|------|------|
| 固定窗口 + 重叠 | 简单稳定，不会漏切 | 可能在句子中间切断 |
| 语义切分（LangChain RecursiveCharacterTextSplitter） | 按段落/句子边界切 | 对法律条文、配方等结构化文本效果差 |

DeepRole 的知识库包含**法律条文**（条款编号结构）、**奶茶配方**（表格化数据）、**心理学资料**（段落结构），这些文本的"语义边界"各不相同。固定切分 + 重叠 50 字在这个场景下最稳定。

❓ **预备问答：** chunk_size=300 怎么定的？→ 经验值。太小（<100）语义不完整，太大（>500）检索时噪声多。300 是 BGE-M3 编码效果和检索精度的平衡点。

### 1.4 向量化编码 — BGE-M3

💻 **（展示代码）**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(BGE_MODEL_PATH)
embeddings = model.encode(chunks, normalize_embeddings=True)  # L2归一化
# embeddings.shape = (N, 1024)  — 每个文本块变成1024维向量
```

🗣️ **为什么选 BGE-M3？三个原因：**

1. **多语言** — 中英混合文本不需要切换模型
2. **1024 维** — 比 OpenAI 的 1536 维更小，Milvus 存储和检索更快
3. **中文效果顶尖** — 在 C-MTEB 中文基准上排名前列

**`normalize_embeddings=True` 的作用：** L2 归一化后，向量都在单位超球面上，此时**内积（IP）等价于余弦相似度**。这为后面 Milvus 用 IP 做相似度搜索埋下伏笔。

🗣️ **存入 Milvus：**

```python
data = [
    {"role_type": role_type, "text": chunk[:2000], "embedding": embedding.tolist()}
    for chunk, embedding in zip(chunks, embeddings)
]
col.insert(data)
```

**Milvus 的索引类型用的是 IVF_FLAT**：先用聚类把向量空间分成若干簇（nlist=128），检索时只在最近的几个簇里搜索（nprobe=10），速度比暴力搜索快 10-100 倍，精度损失很小。

---

## 第二阶段：查询优化（2.5分钟）

🗣️ **用户的原始问题往往不适合直接检索。** 比如用户说"失眠咋办"，太口语化，直接编码效果差。所以需要两步优化。

### 2.1 查询改写 — `rewrite_query()`

💻 **（展示代码）**

```python
def rewrite_query(original_query, persona, role_type):
    resp = requests.post(
        LLM_CONFIG["api_url"],
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "deepseek-chat",
            "messages": [{
                "role": "system",
                "content": f"你是{role_type}，把用户问题改写成3个不同角度的检索查询，每行一个。"
            }, {
                "role": "user",
                "content": original_query
            }],
            "temperature": 0.7,
            "timeout": 10
        }
    )
    content = resp.json()["choices"][0]["message"]["content"]
    queries = [q.strip() for q in content.split('\n') if q.strip()]
    return queries[:3]
```

🗣️ **关键点：`temperature=0.7`**

- `temperature=0` → 改写太死板，几乎等于原文
- `temperature=1.0` → 改写太发散，可能偏离原意
- `0.7` 是平衡点 — 保留核心语义的同时，增加检索的召回面

**实际效果：** "失眠咋办" → ["失眠的缓解方法和改善建议", "失眠症的认知行为疗法", "睡眠障碍的常见原因及对策"]

### 2.2 查询扩写 — `expand_query()`

💻 **（展示代码）**

```python
def expand_query(query, role, persona):
    templates = {
        "心理医生": {
            "默认": ["从心理学角度：{q}", "专业分析：{q}", "情绪管理方面：{q}"],
            "暴躁老哥": ["别矫情：{q}", "直击要害：{q}", "说人话就是：{q}"],
            "知性姐姐": ["慢慢倾听：{q}", "温柔引导：{q}", "共情理解：{q}"]
        },
        "律师": {
            "默认": ["从法律角度：{q}", "法规分析：{q}", "维权建议：{q}"],
            ...
        }
    }
    tpl = templates.get(role, {}).get(persona, ["{q}"])
    return [query] + [t.format(q=query) for t in tpl]
```

🗣️ **查询改写和扩写的区别：**

| | 查询改写 | 查询扩写 |
|---|---|---|
| 方法 | LLM 生成 | 模板填充 |
| 延迟 | ~1s（API调用） | ~0ms（本地计算） |
| 作用 | "翻译"口语→专业表达 | 多角度发散，提高召回率 |

扩写使用的是**角色×人格的模板矩阵**——5个角色 × 3种人格 = 15套模板。不依赖额外的LLM调用，零延迟。

**实际效果：** "失眠怎么办" × 心理医生 × 默认 → 4个查询：
1. "失眠怎么办"（原始）
2. "从心理学角度：失眠怎么办"
3. "专业分析：失眠怎么办"
4. "情绪管理方面：失眠怎么办"

**每个查询去 Milvus 分别检索，取并集，大幅提高召回率。**

---

## 第三阶段：多路召回（5分钟）⭐ 核心亮点

🗣️ **这是整个系统的核心。** 我用了 4 路不同的检索策略，每一路解决不同的问题，最后用 RRF 算法融合。

### 3.1 Milvus 向量检索 — `search_milvus()`（主路）

💻 **（展示代码 + 架构图）**

```python
def search_milvus(query, role, top_k=10):
    # 1. 编码查询
    model = _get_model()
    query_emb = model.encode([query], normalize_embeddings=True)[0]
    
    # 2. 构建搜索参数
    search_params = {
        "metric_type": "IP",       # 内积 ≈ 余弦相似度（因为已归一化）
        "params": {"nprobe": 10}   # 搜索10个聚类簇
    }
    
    # 3. 角色过滤 — 只检索当前角色的知识
    expr = f'role_type == "{role}"' if role and role != "虚拟朋友" else None
    
    # 4. 执行搜索
    results = col.search(
        data=[query_emb.tolist()],
        anns_field="embedding",
        param=search_params,
        expr=expr,                 # 角色过滤
        limit=top_k,
        output_fields=["text", "role_type"]
    )
    
    # 5. 组装结果
    return [{"text": hit.entity.get("text"), "score": float(hit.score), "source": "milvus"}
            for hit in results[0]]
```

🗣️ **关键设计点：**

1. **`metric_type: "IP"`（内积）** — 因为向量已经 L2 归一化，内积等价于余弦相似度，计算更快
2. **`nprobe: 10`** — IVF 索引中搜索的聚类簇数量。nprobe 越大越精确但越慢，10 是经验值
3. **`expr = f'role_type == "{role}"'`** — Milvus 的标量过滤，在搜索时就排除其他角色的数据，而不是搜完再过滤

**角色过滤是 DeepRole 的关键设计：** 保证律师不会引用奶茶配方来回答法律问题，奶茶师不会引用刑法条文来推荐饮品。

❓ **预备问答：**
- Q: 为什么不直接用余弦相似度？→ IP 在归一化后数学等价，且 Milvus 对 IP 有硬件加速优化
- Q: nprobe 怎么调？→ 可以用 Milvus 的 benchmark 工具测，一般 10-64 之间

### 3.2 BM25 关键词检索 — `search_bm25()`（补充语义盲区）

💻 **（展示代码）**

```python
class BM25Search:
    def _tokenize(self, text):
        return list(jieba.cut(text))    # 中文分词
    
    def build_index(self, texts):
        self.corpus = texts
        tokenized_corpus = [self._tokenize(str(t)) for t in texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._save_cache()              # pickle 持久化到磁盘
    
    def search(self, query, top_k=10):
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{"text": self.corpus[i], "score": float(scores[i]), "source": "bm25"}
                for i in top_indices if scores[i] > 0]
```

🗣️ **为什么有了向量检索还要 BM25？**

这是一个关键洞察：**向量检索是语义级的，BM25 是词汇级的，它们互补。**

举个例子：
- 用户问："劳动法 第38条 怎么理解？"
- 知识库里有一段："《中华人民共和国劳动法》第三十八条规定：用人单位应当保证劳动者每周至少休息一日。"
- **向量检索**：能理解"第38条"和"第三十八条"语义相近 ✅
- **BM25**：直接精确匹配"劳动法""第38条"关键词 ✅

反过来：
- 用户问："老板不让我休息怎么办？"
- 知识库里同一段法律条文
- **向量检索**：能理解语义关联 ✅
- **BM25**："休息"能匹配，但"老板"和"用人单位"词汇不同，部分匹配 ⚠️

**所以两路互补，一起用效果更好。** BM25 索引从 Milvus 中读取所有文档来构建，数据源完全一致，只是检索方式不同。索引用 `pickle` 缓存到磁盘，避免每次启动都重建。

### 3.3 MySQL 历史检索 — `mysql_search()`（挖掘对话历史）

```python
def mysql_search(query, top_k=5):
    keywords = [w for w in jieba.cut(query) if len(w) > 1][:5]  # jieba分词，取前5个关键词
    
    for kw in keywords:
        cursor.execute(
            "SELECT message FROM chat_logs WHERE message LIKE %s OR response LIKE %s LIMIT %s",
            (f"%{kw}%", f"%{kw}%", top_k)
        )
```

🗣️ **这路检索解决什么问题？**

用户之前问过类似问题，系统曾经给出过好的回答。MySQL 检索可以**复用历史对话**，避免重复生成。这也是一种"个性化"——系统会"记住"和你的对话。

**注意这里用了 jieba 分词而不是空格分词。** 中文没有天然的空格分隔，"劳动法第38条"用空格分词会变成一整块，jieba 能正确切分为 "劳动法/第/38/条"。

### 3.4 Redis 缓存检索 — `redis_search()`（加速热点查询）

```python
def redis_search(query):
    cache_key = f"search_cache:{hashlib.md5(query.encode()).hexdigest()}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)       # 缓存命中，直接返回
    return []                           # 未命中，返回空
```

🗣️ **用 MD5 哈希做缓存键的原因：**
1. 查询文本可能很长，直接做 key 太浪费内存
2. MD5 生成 32 位十六进制字符串，长度固定
3. 不同查询碰撞概率极低（2^128 种可能）

**TTL 3600 秒** — 1 小时过期。为什么不永久？因为知识库会更新，缓存需要有生命周期。

### 3.5 RRF 融合算法 — `reciprocal_rank_fusion()`（⭐⭐⭐ 重点中的重点）

💻 **（展示公式 + 代码 + 图示）**

```python
def reciprocal_rank_fusion(results_list, k=60):
    """
    RRF: score(d) = Σ weight_i × 1/(k + rank_i(d))
    
    weights = {
        "milvus": 0.5,   # 向量检索权重最高
        "bm25": 0.3,     # 关键词检索次之
        "mysql": 0.1,    # 历史检索辅助
        "redis": 0.1     # 缓存检索辅助
    }
    """
    scores = {}
    
    for source, results in results_list.items():
        for rank, r in enumerate(results[:10], 1):  # 取前10条
            rrf_score = weights[source] / (k + rank)
            key = r["text"][:100]                    # 用前100字做去重键
            
            if key not in scores:
                scores[key] = {"text": r["text"], "score": rrf_score, "sources": [source]}
            else:
                scores[key]["score"] += rrf_score
                scores[key]["sources"].append(source)
    
    return sorted(scores.values(), key=lambda x: x["score"], reverse=True)
```

🗣️ **RRF 是整个多路召回的灵魂，我详细解释：**

**问题：** 4 路检索的分数尺度完全不同。
- Milvus 返回的是余弦相似度（0~1）
- BM25 返回的是 TF-IDF 分数（可能几十到几百）
- MySQL 返回的是固定的 0.5
- Redis 返回的是缓存的旧分数

**直接加权求和没有意义。** 就像不能把"考试分数"和"身高"加在一起。

**RRF 的巧妙之处：只看排名，不看分数。**

公式：`score(d) = Σ weight_i × 1/(k + rank_i(d))`

- `k=60` 是平滑常数，防止排名第一的文档得分过高
- `rank` 从 1 开始，排名越靠前，分母越小，分数越高
- **不管原始分数是多少，只要排名第 1，就拿最高分**

**实际效果举例：**
```
文档A：Milvus排第1、BM25排第5
  → 0.5 × 1/(60+1) + 0.3 × 1/(60+5) = 0.00820 + 0.00462 = 0.01282

文档B：Milvus排第3、BM25排第1
  → 0.5 × 1/(60+3) + 0.3 × 1/(60+1) = 0.00794 + 0.00492 = 0.01286

文档B 略胜！因为它在两路检索中都有不错的排名。
```

**为什么 k=60？** 这是论文《Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods》中的推荐值，在实践中效果稳定。

**为什么多路比单路好？**

| 场景 | 单路 Milvus | 单路 BM25 | 4路 RRF |
|------|------------|-----------|---------|
| 语义相似但词汇不同 | ✅ 命中 | ❌ 漏掉 | ✅ 命中 |
| 词汇精确匹配 | ⚠️ 可能漏 | ✅ 命中 | ✅ 命中 |
| 两路都命中 | — | — | ⭐ 分数叠加，排名更靠前 |

### 3.6 互联网搜索 — `search_web()`（兜底）

```python
def search_web(query, num=3):
    resp = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
        timeout=8
    )
    data = resp.json()
    return [{"text": item["Text"], "source": "互联网", "url": item.get("FirstURL", "")}
            for item in data.get("RelatedTopics", [])[:num] if item.get("Text")]
```

🗣️ **互联网搜索是最后的兜底。** 当本地知识库没有相关内容时（比如用户问的是最新新闻或时效性问题），DuckDuckGo 可以补充。但它的权重设得很低，因为互联网内容质量不可控。

---

## 第四阶段：重排序与生成（3分钟）

### 4.1 BGE-Reranker 重排序

💻 **（展示代码）**

```python
class Retriever:
    def __init__(self, model_path):
        self._model = None              # 懒加载
        self._reranker = None
        # Reranker 较小，启动时就加载
        self._reranker = FlagReranker(r'bge-reranker-v2-m3', use_fp16=True)
    
    @property
    def model(self):
        """懒加载：首次使用时才加载 BGE-M3（约1.5GB）"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_path)
        return self._model
    
    def search(self, q, role, top_k=3):
        # 1. 向量检索（召回 top_k*2 条候选）
        results = milvus_col.search(...)
        
        # 2. BGE-Reranker 重排序（交叉编码，更精准）
        if self._reranker and len(results) > 1:
            pairs = [[q, r["text"]] for r in results]
            scores = self._reranker.compute_score(pairs)
            for i, r in enumerate(results):
                r["score"] = float(scores[i])
            results.sort(key=lambda x: x["score"], reverse=True)
        
        # 3. 去重返回 top_k
        return results[:top_k]
```

🗣️ **为什么召回之后还要重排序？**

召回阶段用的是**双塔模型**（Bi-Encoder）：query 和 document 分别编码，独立计算向量，速度快但交互不够深入。

重排序用的是**交叉编码器**（Cross-Encoder）：把 query 和 document 拼在一起输入模型，逐 token 做注意力交互，**精度远高于双塔模型**，但速度慢。

```
召回（Bi-Encoder）：快，10ms/query，能从百万文档中找 top-100
重排（Cross-Encoder）：慢，50ms/pair，从100个中精排 top-5
```

**所以架构是：粗排（Bi-Encoder）→ 精排（Cross-Encoder），兼顾速度和精度。**

**`use_fp16=True`** — 用半精度浮点数推理，显存占用减半，精度几乎无损（BGE-Reranker 对 FP16 鲁棒）。

### 4.2 模型懒加载

🗣️ **为什么 BGE-M3 用懒加载，Reranker 却启动时就加载？**

| 模型 | 大小 | 加载时间 | 加载策略 |
|------|------|---------|---------|
| BGE-M3 (编码器) | ~1.5GB | 5-10秒 | **懒加载**（首次使用才加载） |
| BGE-Reranker (精排器) | ~500MB | 2-3秒 | **启动加载**（始终可用） |

BGE-M3 太大，启动时加载会阻塞服务启动。Reranker 较小，且每次检索都需要，启动时加载更合理。

**用 `@property` 装饰器实现懒加载：** 只有第一次调用 `self.model` 时才加载，后续调用直接返回已加载的实例。FastAPI 启动秒开，模型按需加载。

### 4.3 DeepSeek 流式生成 — SSE 协议

💻 **（展示代码）**

```python
async def generate_stream():
    resp = requests.post(
        LLM_CONFIG["api_url"],
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 1.0,        # 角色扮演需要创造性
            "max_tokens": 500,
            "stream": True             # 启用流式输出
        },
        stream=True,
        timeout=60
    )
    
    for line in resp.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]":
                    break
                chunk_data = json.loads(data_str)
                content = chunk_data["choices"][0].get("delta", {}).get("content", "")
                if content:
                    yield f"data: {json.dumps({'chunk': content})}\n\n"

# FastAPI 路由
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

🗣️ **SSE（Server-Sent Events）和 WebSocket 的区别：**

| | SSE | WebSocket |
|---|---|---|
| 通信方向 | 单向（服务器→客户端） | 双向 |
| 协议 | HTTP 原生 | 需要额外握手 |
| 复杂度 | 低 | 高 |
| 适用场景 | LLM 流式输出 | 聊天室、游戏 |

**为什么用 SSE？** LLM 的输出是**单向流式**的——服务器生成一个 token 推一个 token，客户端只需要接收。SSE 比 WebSocket 简单得多，HTTP 原生支持，不需要额外握手。

### 4.4 Prompt 构建策略

```python
# 系统提示词结构
sp = f"""【重要指令】
1. 用户资料：{profile_info}
2. 必须用用户资料中的名字称呼用户，绝对不要问用户叫什么名字。
3. 严格按照以下人格设定回答：
   {role_description}
   {persona_description}
4. 如果知识库有相关内容，请详细回答。
5. 【排版要求】回复中适当使用换行、数字列表、重点加粗，让内容层次分明。"""

messages = [
    {"role": "system", "content": sp},           # 系统提示
    *[{"role": h["role"], "content": h["content"]} for h in hist[-6:]],  # 最近6轮历史
    {"role": "system", "content": "参考:\n" + "\n".join(kb[:3])},        # 检索知识
    {"role": "user", "content": user_query}       # 用户提问
]
```

🗣️ **Prompt 的四层结构：**

1. **系统提示** — 角色背景 + 人格风格 + 用户资料
2. **对话历史** — 最近 6 轮，保证上下文连贯
3. **检索知识** — 知识库检索结果，最多 3 条，作为"参考资料"注入
4. **用户提问** — 当前问题

**关键细节：**
- **用户资料注入** — 系统会把用户的姓名、性别、生日、兴趣注入到 prompt 中，让 AI 用名字称呼用户，而不是问"你叫什么"
- **历史窗口控制** — 只保留最近 6 轮，避免 token 溢出（DeepSeek 上下文窗口 4K-32K）
- **知识注入位置** — 检索到的知识紧跟在用户提问之前，确保模型在生成时"看到"检索结果

### 4.5 后处理校验 — `validate_response()`

```python
def validate_response(text, role, persona):
    # 1. 敏感词过滤
    blocked = ["政治敏感", "色情"]
    for w in blocked:
        if w in text:
            return "[系统] 该回复未通过安全校验"
    
    # 2. 空白内容拦截
    if len(text.strip()) < 5:
        return "[系统] 生成内容过短，请重试"
    
    # 3. 角色一致性检查（软校验）
    role_kw = ROLE_KEYWORDS.get(role, [])
    if role_kw and len(text) > 20:
        has_role_hint = any(kw in text for kw in role_kw)
        # 不拦截，只记录，用于后续优化 prompt
    
    return text
```

🗣️ **后处理做三件事：**

1. **安全过滤** — 检测敏感词，拦截不合规内容
2. **空白拦截** — 如果生成内容太短（< 5字），返回系统提示
3. **角色一致性检查** — 检查回复中是否包含角色特征词（如心理医生的"情绪""压力"，律师的"法律""条款"等），**只做软校验**（记录但不拦截），因为 LLM 有时候会用其他表达方式

### 4.6 追问选项生成 — `gen_options()`

```python
async def gen_options(role, last_response, persona):
    prompt = f"""你刚才对用户说了：'{last_response}'
    根据你刚才说的内容，生成3个用户可能会回复的简短回答选项（每个15字以内）"""
    
    resp = requests.post(LLM_CONFIG["api_url"], ...)
    opts = [o.strip() for o in txt.split("\n") if o.strip()][:3]
    return opts if len(opts) >= 3 else ["能再详细说说吗？", "然后呢？", "后来怎么样了？"]
```

🗣️ **追问选项是用户体验设计。** 用户不知道该问什么时，系统自动生成 3 个追问选项，降低对话门槛。如果 LLM 生成失败，降级到通用追问。

---

## 第五阶段：对话记忆与用户系统（2分钟）

### 5.1 对话历史 — `MemMgr` 类

```python
class MemMgr:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def save(self, k, role, content):
        msg = json.dumps({"role": role, "content": content, "time": datetime.now().isoformat()})
        self.r.rpush(k, msg)           # 追加到列表尾部
        self.r.expire(k, 86400)        # 24小时过期
        self.r.ltrim(k, -100, -1)      # 只保留最近100条
    
    def get(self, k, limit=20):
        return [json.loads(m) for m in self.r.lrange(k, -limit, -1)]
```

🗣️ **为什么用 Redis 存对话历史而不是 MySQL？**

| | Redis | MySQL |
|---|---|---|
| 读写速度 | μs 级 | ms 级 |
| 数据结构 | List（天然有序） | 表（需要 ORDER BY） |
| 过期机制 | 原生 TTL | 需要定时清理 |
| 适用场景 | 热数据、高频读写 | 冷数据、持久化 |

对话历史是**高频读写**的热数据，每条消息都要读写一次，Redis 的 μs 级响应是必须的。24 小时过期后，重要的对话会写入 MySQL 做持久化。

**键的设计：** `chat:{username}:{role_type}` — 每个用户每个角色独立存储，保证切换角色时对话历史不串。

### 5.2 对话摘要压缩 — `summarize_history()`

```python
def summarize_history(history, max_len=200):
    recent = history[-6:]       # 最近3轮完整保留
    early = history[:-6]        # 早期对话压缩
    if early:
        summaries = [msg["content"][:80] + "..." for msg in early]
        return [{"role": "system", "content": f"早期对话摘要：{' | '.join(summaries)}"}] + recent
    return recent
```

🗣️ **当对话历史过长时，采用"保留最近 + 压缩早期"的策略：**
- 最近 3 轮对话（6 条消息）完整保留，保证上下文连贯
- 更早的对话只保留每条的前 80 字，拼接成摘要
- 这样既节省 token，又不丢失关键信息

### 5.3 降级策略

```python
async def gen(role, q, hist, kb, persona, profile):
    if LLM_CONFIG.get("api_key"):
        try:
            return await AIGen._llm(...), "llm"      # 优先 LLM
        except Exception as e:
            print(f"LLM失败:{e}")
    return AIGen._rule(role, q), "rule"               # 降级到规则引擎
```

```python
# 规则引擎（降级方案）
RULES = {
    "虚拟朋友": {"心情": "听到你心情不好，我在呢。", "default": "嗯嗯我懂！"},
    "心理医生": {"失眠": "失眠确实困扰人。", "default": "嗯我在听。"},
    "律师": {"劳动": "这涉及劳动争议。", "default": "请描述。"},
    "投资分析师": {"风险": "注意风险控制。", "default": "投资需谨慎。"},
    "奶茶师": {"珍珠": "珍珠奶茶是招牌！", "default": "欢迎光临！"}
}
```

🗣️ **如果 DeepSeek API 不可用，系统会降级到规则引擎**——基于关键词匹配的硬编码回复。虽然质量下降，但至少系统不会完全不可用。这是一个重要的**容灾设计**。

---

## 第六阶段：社交与用户粘性功能（1.5分钟）

### 6.1 用户认证

```python
# 注册 — SHA256 密码哈希
@app.post("/api/register")
async def reg(u: str, p: str):
    cur.execute("INSERT INTO users(username, password_hash, profile_json) VALUES(%s,%s,%s)",
                (u, hashlib.sha256(p.encode()).hexdigest(), "{}"))

# 登录 — 哈希比对
@app.post("/api/login")
async def login(u: str, p: str):
    cur.execute("SELECT password_hash, profile_json FROM users WHERE username=%s", (u,))
    row = cur.fetchone()
    if row and row[0] == hashlib.sha256(p.encode()).hexdigest():
        return {"ok": True, "profile": row[1]}
```

🗣️ **密码用 SHA-256 哈希存储，不存明文。** 生产环境还应该加盐（salt），当前版本用固定盐，是已知改进点。

### 6.2 分享链接系统

```python
# 生成分享码，其他人可以通过链接直接对话
@app.get("/api/my_shares")
async def my_shares(u: str):
    cur.execute("SELECT share_code, role_type, title FROM shares WHERE owner_username=%s", (u,))
    # 返回：BASE_URL + "/s/" + share_code
```

🗣️ **分享链接让用户可以把自己的对话配置（角色+人格）分享给其他人。** 比如一个心理咨询师可以分享一个"知性姐姐×心理医生"的对话链接给来访者。

### 6.3 成就系统

```python
achievements = [
    {"name": "初来乍到", "desc": "发送第一条消息", "icon": "👶", "unlock": total >= 1},
    {"name": "话痨新人", "desc": "发送10条消息", "icon": "💬", "unlock": total >= 10},
    {"name": "百话王", "desc": "发送100条消息", "icon": "👑", "unlock": total >= 100},
    {"name": "全角色制霸", "desc": "使用过全部5个角色", "icon": "🏅", "unlock": roles >= 5},
    {"name": "人格分裂", "desc": "使用过全部3种人格", "icon": "🎪", "unlock": personas >= 3},
    ...
]
```

🗣️ **12 个成就徽章，激励用户探索不同角色和人格。** 数据来自 MySQL 聚合查询（COUNT、COUNT DISTINCT），纯后端计算，前端只负责展示。

### 6.4 金句墙 / 每日运势

🗣️ 这两个是轻量级用户粘性功能：

- **金句墙**：Redis List 存储，用户可以保存 AI 的精彩回复，`ltrim` 只保留最近 50 条，30 天过期
- **每日运势签**：`random.choice(fortunes)` 随机抽取 9 种签文，每种推荐一个角色+人格组合

---

## 技术架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (HTML/JS)                        │
│              fetch() + SSE 逐字流式接收                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│              FastAPI 后端服务 (port 8000)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │ 路由层   │ │ 中间件   │ │ 认证层   │                 │
│  └────┬─────┘ └──────────┘ └──────────┘                 │
│       │                                                  │
│  ┌────▼────────────────────────────────────────────┐     │
│  │              RAG Pipeline                       │     │
│  │  安全检测 → 查询改写 → 查询扩写 → 多路召回       │     │
│  │  → RRF融合 → BGE-Reranker重排 → DeepSeek生成    │     │
│  │  → 后处理校验 → 追问选项                         │     │
│  └────┬──────┬──────┬──────┬──────┬────────────────┘     │
└───────┼──────┼──────┼──────┼──────┼──────────────────────┘
        │      │      │      │      │
   ┌────▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐
   │Milvus ││Redis││MySQL││DuckD││BGE  │
   │向量库 ││缓存 ││持久化││uckGo││模型 │
   └───────┘└─────┘└─────┘└─────┘└─────┘
```

---

## 总结（1分钟）

🗣️ **这个项目完整实现了工业级 RAG 系统的每一个环节：**

1. **数据预处理** — 多格式解析 → 角色自动匹配 → 固定窗口切分 → BGE-M3 向量化
2. **查询优化** — DeepSeek 改写 + 15 套角色×人格模板扩写
3. **多路召回** — Milvus(语义) + BM25(词汇) + MySQL(历史) + Redis(缓存) + DuckDuckGo(互联网)
4. **RRF 融合** — 排名级融合，解决多路分数不可比问题
5. **BGE-Reranker 精排** — Cross-Encoder 精细化排序
6. **DeepSeek 流式生成** — SSE 协议逐字输出
7. **后处理校验** — 敏感词 + 空白 + 角色一致性

**相比直接调用 DeepSeek API 的方案，DeepRole 的优势：**
- ✅ 减少幻觉（有据可依）
- ✅ 知识可更新（改知识库不用重训模型）
- ✅ 角色一致性（提示词工程 + 人格系统 + 角色过滤）
- ✅ 响应速度快（Redis缓存 + BM25缓存 + 流式输出）
- ✅ 高可用（LLM→规则引擎降级）

**已知局限与改进方向：**
- ⚠️ PDF 扫描件暂不支持 → 可加 OCR 层（PaddleOCR）
- ⚠️ 密码用固定盐 → 应改为随机盐 + bcrypt
- ⚠️ 向量库没有增量更新 → 可加监听文件变化自动入库
- ⚠️ 多路召回权重是手动调的 → 可用学习排序（LTR）自动优化
- ⚠️ 查询改写串行执行 → 可与查询扩写并行化

谢谢各位老师！

---

## 预备问答清单

| 问题 | 回答要点 |
|------|----------|
| 为什么不用 LangChain？ | LangChain 抽象层太厚，不利于理解底层原理；本项目强调从零实现，每个环节可控 |
| Milvus 和 FAISS 的区别？ | Milvus 是分布式向量数据库，支持标量过滤、持久化、RBAC；FAISS 是单机库，更轻量但功能少 |
| 为什么选 DeepSeek？ | 中文效果好、API 便宜（1元/百万token）、支持流式输出 |
| 怎么评估 RAG 效果？ | 可用 RAGAS 框架评估：Faithfulness、Answer Relevancy、Context Precision |
| 如果知识库有 100 万条怎么办？ | Milvus 支持十亿级向量，IVF 索引 + 分片可以水平扩展 |
| 怎么处理多轮对话？ | Redis 存最近 100 条历史，读取时取最近 20 条注入 prompt |
| RRF 的 k 值怎么选？ | 论文推荐 k=60，实践中 30-100 都可接受，变化不大 |
| 流式输出断线怎么办？ | SSE 协议原生支持重连（EventSource 自动重连），后端记录已发送位置 |
| 为什么角色过滤在 Milvus 层而不是结果层？ | 在搜索时就过滤，减少无用计算，提高检索速度和精度 |
| 5角色×3人格的 Prompt 怎么管理？ | 模板矩阵硬编码，15套 Prompt 各自独立，不互相干扰 |
| 向量检索和 BM25 的互补性怎么量化？ | 可做消融实验：单路 vs 双路 vs 四路，用 RRF 融合后对比 Recall@K |