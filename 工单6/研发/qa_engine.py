"""
工单06 - 混合检索问答引擎
向量检索(FAISS) + 全文检索(BM25) + 混合检索
支持中文和英文问答 | 3种重排算法
目标：准确率≥90%，召回率≥95%

工单编号：人工智能NLP-RAG-混合检索任务
"""
import sys
import json
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from config import LLM_API_URL, LLM_MODEL, TOP_K, EVAL_QUESTIONS, VECTOR_DB_PATH
from hybrid_retriever import HybridRetriever, detect_language


class HybridRAGEngine:
    """混合检索RAG引擎（中英双语）"""
    
    def __init__(self, retrieval_mode="hybrid"):
        """
        retrieval_mode:
            "vector"   - 仅向量检索
            "fulltext" - 仅全文检索
            "hybrid"   - 混合检索（默认）
        """
        self.retrieval_mode = retrieval_mode
        self.retriever = HybridRetriever()
        self.retriever.load_vector_store(VECTOR_DB_PATH)
        self.retriever.load_embedding_model()
        
        # 加载chunks初始化BM25
        mapping_path = VECTOR_DB_PATH / "chunk_mapping.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        self.retriever.init_bm25(chunks)
        
        self.rerank_methods = ["tfidf", "position", "diversity"]
        
        print(f"检索模式: {retrieval_mode}, 重排算法: {', '.join(self.rerank_methods)}")
    
    def retrieve(self, query, top_k=TOP_K):
        """根据当前模式执行检索（中英双语）"""
        if self.retrieval_mode == "vector":
            results = self.retriever.vector_only(query, top_k)
        elif self.retrieval_mode == "fulltext":
            results = self.retriever.fulltext_only(query, top_k)
        else:  # hybrid
            results = self.retriever.hybrid_search(query, top_k, self.rerank_methods)
        
        return results
    
    def switch_mode(self, mode):
        """切换检索模式"""
        if mode in ["vector", "fulltext", "hybrid"]:
            self.retrieval_mode = mode
            return True
        return False
    
    def generate(self, query, context_chunks):
        """基于检索结果生成答案（中英双语）"""
        lang = detect_language(query)
        
        context = "\n\n".join([
            f"[第{c['page_num']}页] {c['text'][:800]}"
            for c in context_chunks
        ])
        
        # 根据语言选择prompt模板
        if lang == "en":
            prompt = f"""You are a document-based Q&A assistant. Answer the question based on the provided document content.

Document Content:
{context}

Question: {query}

Requirements:
1. Answer ONLY based on the provided document content
2. If the information is not found in the documents, state "Information not found in the documents"
3. Cite the source (page number)
4. Answer concisely and accurately

Answer:"""
        else:
            prompt = f"""你是一个基于PDF文档的问答助手（中英双语）。请根据以下文档内容回答问题。

文档内容：
{context}

问题：{query}

要求：
1. 仅基于提供的文档内容回答
2. 如果文档中没有相关信息，请明确说明"文档中未找到相关信息"
3. 引用信息来源（页码）
4. 回答简洁准确
5. 使用与问题相同的语言回答

回答："""
        
        try:
            response = requests.post(
                LLM_API_URL,
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 500
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "生成失败")
            else:
                return f"LLM请求失败: {response.status_code}"
        except Exception as e:
            return f"LLM连接失败: {e}"
    
    def answer(self, query):
        """完整的问答流程（中英双语）"""
        start = time.time()
        lang = detect_language(query)
        
        # 1. 检索
        retrieval_start = time.time()
        results = self.retrieve(query)
        retrieval_time = time.time() - retrieval_start
        
        # 2. 生成
        gen_start = time.time()
        answer = self.generate(query, results)
        gen_time = time.time() - gen_start
        
        total_time = time.time() - start
        
        return {
            "query": query,
            "answer": answer,
            "language": lang,
            "retrieval_mode": self.retrieval_mode,
            "retrieved_chunks": [{"chunk_id": c["chunk_id"], "score": round(c["score"], 4), "methods": c.get("methods", ["unknown"])} 
                                  for c in results[:3]],
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(gen_time, 3),
            "total_time": round(total_time, 3)
        }
    
    def compare_retrieval_modes(self, query):
        """对比三种检索模式的结果"""
        results = {}
        for mode in ["vector", "fulltext", "hybrid"]:
            self.switch_mode(mode)
            r = self.retrieve(query, TOP_K * 2)
            results[mode] = {
                "count": len(r),
                "top_scores": [round(c["score"], 4) for c in r[:3]],
                "chunk_ids": [c["chunk_id"] for c in r[:3]],
                "methods": [c.get("methods", ["unknown"]) for c in r[:3]],
            }
        return results


def run_interactive():
    """交互式问答模式"""
    engine = HybridRAGEngine("hybrid")
    print("\n" + "=" * 60)
    print("📝 工单06 - 混合检索问答引擎（中英双语）")
    print("   命令: /mode vector|fulltext|hybrid 切换检索模式")
    print("   命令: /compare <query> 对比三种模式")
    print("   输入 'exit' 退出")
    print("=" * 60)
    
    while True:
        query = input("\n💬 问题: ").strip()
        if query.lower() in ["exit", "quit", "q"]:
            break
        
        if query.startswith("/mode "):
            mode = query.split(" ", 1)[1]
            if engine.switch_mode(mode):
                print(f"  已切换到 {mode} 模式")
            else:
                print(f"  无效模式: {mode} (可选: vector/fulltext/hybrid)")
            continue
        
        if query.startswith("/compare "):
            q = query.split(" ", 1)[1]
            print(f"\n🔍 对比三种检索模式: {q}")
            results = engine.compare_retrieval_modes(q)
            for mode, r in results.items():
                print(f"  [{mode}] 返回{r['count']}条, 分数: {r['top_scores']}")
            continue
        
        if not query:
            continue
        
        result = engine.answer(query)
        print(f"\n📋 答案: {result['answer'][:300]}")
        print(f"🌐 语言: {result['language']} | 📡 模式: {result['retrieval_mode']}")
        print(f"⚡ 耗时: {result['total_time']:.3f}s")
        if result['retrieved_chunks']:
            print(f"📎 来源: {', '.join([c['chunk_id'] for c in result['retrieved_chunks'][:3]])}")


def run_evaluation():
    """运行评估测试"""
    engine = HybridRAGEngine("hybrid")
    
    results = []
    for q in EVAL_QUESTIONS:
        print(f"\n{'='*60}")
        print(f"问题 [{q['id']}]: {q['question']}")
        
        # 混合检索
        engine.switch_mode("hybrid")
        hybrid_result = engine.answer(q["question"])
        print(f"混合检索: {hybrid_result['answer'][:200]}")
        
        results.append({
            "id": q["id"],
            "question": q["question"],
            "language": hybrid_result["language"],
            "retrieval_mode": "hybrid",
            "answer": hybrid_result["answer"],
            "retrieval_time": hybrid_result["retrieval_time"],
            "total_time": hybrid_result["total_time"],
        })
    
    # 保存结果
    output_path = BASE_DIR / "logs" / "hybrid_eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n评估结果已保存: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_evaluation()
    else:
        run_interactive()
