"""
QA引擎 —— RAG问答的"大脑"

这个模块是整个系统的核心，它完成RAG的完整链路：
  用户问题 → 向量检索 → 上下文构建 → LLM生成答案

支持双LLM引擎：
  1. Ollama (qwen2.5 本地模型，首选项)
  2. DeepSeek API (云端回退，当Ollama不可用时自动切换)
"""
import time, json, urllib.request

from config import (OLLAMA_BASE, LLM_MODEL, TOP_K,
                    DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL,
                    USE_DEEPSEEK_FALLBACK)


class QAEngine:
    """
    RAG问答引擎 —— 负责"检索→生成"全过程。

    用法:
        store = MilvusStore()
        qa = QAEngine(store)
        result = qa.answer("武汉力源发行股数是多少？")
        # result 包含: answer, retrieved_chunks, timing...
    """

    def __init__(self, store):
        """
        初始化QA引擎。

        参数:
            store: MilvusStore 实例（已经连接好Milvus的）

        注意：store是外部传入的，不是内部创建的。
        这样做的好处是：多个QAEngine可以共享同一个Milvus连接。
        """
        self.store = store
        self.llm_url = f"{OLLAMA_BASE}/api/chat"

    # ====================================================================
    # 第一步：检索（Retrieval）
    # ====================================================================
    def retrieve(self, query, top_k=TOP_K):
        """
        从Milvus向量库中检索与query最相关的文档块。

        参数:
            query: 用户问题字符串
            top_k: 返回多少条结果（默认10条）

        返回:
            (results, elapsed_time) 元组
            - results: 检索到的文档块列表，每个块包含 text/page_num/pdf_name/score
            - elapsed_time: 检索耗时（秒）
        """
        start = time.time()
        # 实际检索工作委托给 MilvusStore.search()
        # search()内部做了两件事：向量检索 + 关键词兜底（hybrid模式）
        results = self.store.search(query, top_k=top_k)
        elapsed = time.time() - start
        return results, elapsed

    # ====================================================================
    # 第二步：构建上下文（Context Building）
    # ====================================================================
    def _build_context(self, context_chunks, max_chunks=5):
        """
        把检索到的文档块拼接成一段文字，作为LLM的"参考材料"。

        为什么取Top-5而不是Top-10？
        - 太多chunks会让LLM的上下文超出限制
        - 太多噪声会干扰LLM的判断
        - 经测试Top-5在精度和上下文长度之间取得最佳平衡

        参数:
            context_chunks: 检索结果列表
            max_chunks: 最多取前几个chunk（默认5个）

        返回:
            拼接好的上下文字符串，格式如：
            "[Page 10, 招股说明书1] 发行股数为1,670万股..."
        """
        context_parts = []
        for c in context_chunks[:max_chunks]:
            # 标注来源页码和PDF名称，方便LLM引用
            source = f"[Page {c['page_num']}, {c['pdf_name']}]"
            # 每个chunk最多取前400字，避免超长
            context_parts.append(f"{source} {c['text'][:400]}")
        return "\n\n".join(context_parts)

    # ====================================================================
    # DeepSeek API 回退生成（备用方案）
    # ====================================================================
    def _generate_via_deepseek(self, query, context_chunks):
        """
        通过DeepSeek云端API生成答案。
        当Ollama本地模型不可用时，自动切换到这里。

        优点：稳定可靠，不需要本地GPU
        缺点：需要联网，有API调用费用
        """
        # 构建参考上下文（只用Top-5）
        context = self._build_context(context_chunks, max_chunks=3)

        # 构造ChatML格式的消息
        # system: 设定AI角色和行为规则
        # user: 提供文档内容+问题
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文档问答助手。"
                           "只根据提供的文档内容回答问题，引用来源页码，用中文简洁回答。"
            },
            {
                "role": "user",
                "content": f"文档内容：\n{context}\n\n问题：{query}"
            }
        ]

        # 构造API请求
        data = json.dumps({
            "model": DEEPSEEK_MODEL,       # deepseek-chat
            "messages": messages,
            "temperature": 0.05,           # 低温度=更确定的回答
            "max_tokens": 300,             # 答案最长300个token
            "stream": False                # 非流式，一次性返回
        }).encode()

        # 发送HTTP请求到DeepSeek API
        req = urllib.request.Request(
            DEEPSEEK_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        # 从API响应中提取生成的文本
        return result["choices"][0]["message"]["content"]

    # ====================================================================
    # 第三步：生成（Generation）
    # ====================================================================
    def generate(self, query, context_chunks):
        """
        基于检索到的文档块，让LLM生成答案。

        策略：
        1. 先尝试 Ollama（本地，速度快）
        2. 如果Ollama返回空或出错 → 切到 DeepSeek API

        这种"本地优先+云端回退"的模式叫"双引擎架构"，
        既保证了速度（Ollama正常时），又保证了可用性（Ollama挂了也有救）。
        """
        # 构建上下文
        context = self._build_context(context_chunks, max_chunks=3)

        # 构造Prompt（提示词）
        # 这里用了"少样本提示"的思路，明确告诉LLM要做什么、不要做什么
        prompt = (
            "根据以下文档内容回答问题。\n\n"
            f"文档内容：\n{context}\n\n"
            f"问题：{query}\n\n"
            "要求：\n"
            "1. 只根据文档内容回答\n"
            "2. 注意文档中的分类标签，确保回答与问题指向的分类一致\n"
            "3. 引用来源页码\n"
            "4. 用中文简洁回答\n"
            "答案："
        )

        # ---- 尝试1: Ollama ----
        try:
            data = {
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.05, "num_predict": 200}
            }
            req = urllib.request.Request(
                self.llm_url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=20)
            result = json.loads(resp.read())
            ollama_response = result.get("message", {}).get("content", "")

            # 如果Ollama返回了有效内容，直接用
            if ollama_response and len(ollama_response) > 10:
                return ollama_response

            # Ollama返回空或太短 → 尝试DeepSeek
            if USE_DEEPSEEK_FALLBACK:
                return self._generate_via_deepseek(query, context_chunks)
            return ollama_response or "Generation failed"

        except Exception as e:
            # ---- 尝试2: DeepSeek API（Ollama报错后的回退） ----
            if USE_DEEPSEEK_FALLBACK:
                try:
                    return self._generate_via_deepseek(query, context_chunks)
                except Exception as e2:
                    # 两个引擎都挂了，返回错误信息
                    return (f"(LLM生成失败 - Ollama: {str(e)[:50]}; "
                            f"DeepSeek: {str(e2)[:50]})")
            return f"(Ollama不可用，DeepSeek回退未开启) {str(e)[:80]}"

    def _call_llm(self, prompt):
        """直接用 prompt 调用 LLM，不走 RAG 检索流程（供图像分析等模块使用）"""
        try:
            data = {"model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 250}}
            req = urllib.request.Request(
                self.llm_url, data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read()).get("message", {}).get("content", "")
        except Exception as e:
            if USE_DEEPSEEK_FALLBACK:
                try:
                    return self._generate_via_deepseek(prompt, [])
                except:
                    pass
            return f"[LLM unavailable: {str(e)[:60]}]"

    # ====================================================================
    # 完整RAG流程：检索 + 生成（单轮问答）
    # ====================================================================
    def answer(self, query):
        """
        完整的RAG问答流程——给一个问题，返回完整结果。

        这个方法把"检索"和"生成"两步串起来，
        还记录每一阶段的耗时（用于WO13性能分析）。

        参数:
            query: 用户问题

        返回:
            dict 包含:
            - query: 原始问题
            - answer: LLM生成的答案文本
            - retrieved_chunks: 检索到的文档块（前5个）
            - retrieval_time: 检索耗时
            - llm_time: LLM生成耗时
            - total_time: 总耗时
        """
        t0 = time.time()

        # Step 1: 检索
        results, retrieval_time = self.retrieve(query)
        t1 = time.time()

        # 如果没有检索到任何内容，直接返回
        if not results:
            return {
                "query": query,
                "answer": "No relevant information found in the document base.",
                "retrieved_chunks": [],
                "retrieval_time": retrieval_time,
                "total_time": time.time() - t0,
                "llm_time": 0,
            }

        # Step 2: 生成
        answer = self.generate(query, results)
        t2 = time.time()

        # Step 3: 组装结果
        return {
            "query": query,
            "answer": answer,
            "retrieved_chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "page_num": c["page_num"],
                    "pdf_name": c["pdf_name"],
                    "score": c["score"],
                    "_source": c.get("_source", "vector"),  # vector 或 keyword
                }
                for c in results[:5]  # 只返回前5个chunk的信息（够用就行）
            ],
            "retrieval_time": round(retrieval_time, 3),
            "llm_time": round(t2 - t1, 3),
            "total_time": round(t2 - t0, 3),
        }

    # ====================================================================
    # 多轮对话版RAG（工单05用）
    # ====================================================================
    def answer_with_history(self, query, history):
        """
        带对话历史的RAG问答——支持多轮对话的指代消解。

        比如用户先问"力源发行股数是多少？"，再问"那兴图新科的呢？"
        第二问如果不加历史，LLM不知道"那"指的是什么。
        所以把最近几轮对话注入到问题中。

        参数:
            query: 当前用户问题
            history: 对话历史列表，格式 [(问, 答), (问, 答), ...]

        返回:
            同answer()的格式
        """
        if history and len(history) > 0:
            # 提取最近3轮对话作为上下文
            recent = " ".join([
                f"Q: {h[0]} A: {h[1][:200]}" for h in history[-3:]
            ])
            # 增强查询 = 历史 + 当前问题
            enhanced_query = f"对话历史: {recent}\n当前问题: {query}"
        else:
            enhanced_query = query

        # 用增强后的查询去检索
        return self.answer(enhanced_query)

    # ====================================================================
    # 批量评估（工单07用）
    # ====================================================================
    def evaluate_questions(self, questions):
        """
        批量评估一组问题。

        参数:
            questions: 问题列表，格式 [{"id": 1, "question": "..."}, ...]

        返回:
            每个问题的答案+耗时信息
        """
        results = []
        for q in questions:
            qid = q["id"]
            question = q["question"]
            answer = self.answer(question)
            results.append({
                "id": qid,
                "question": question,
                "answer": answer["answer"],
                "retrieval_time": answer["retrieval_time"],
                "total_time": answer["total_time"],
                "retrieved_pages": [c["page_num"] for c in answer["retrieved_chunks"]],
            })
        return results
