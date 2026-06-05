"""
工单01 - 问答引擎模块
检索 + LLM生成
"""
import sys
import json
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from config import LLM_API_URL, LLM_MODEL, TOP_K, EVAL_QUESTIONS, VECTOR_DB_PATH

class RAGEngine:
    def __init__(self, embedding_model="BAAI/bge-small-zh-v1.5"):
        self.load_vector_store()
        self.load_embedding_model(embedding_model)
    
    def load_vector_store(self):
        """加载FAISS索引"""
        import faiss
        import numpy as np
        
        index_path = VECTOR_DB_PATH / "faiss_index.bin"
        mapping_path = VECTOR_DB_PATH / "chunk_mapping.json"
        
        self.index = faiss.read_index(str(index_path))
        with open(mapping_path, "r", encoding="utf-8") as f:
            self.chunk_mapping = json.load(f)
        
        print(f"向量库已加载: {self.index.ntotal}个向量, 维度{self.index.d}")
    
    def load_embedding_model(self, model_name):
        from sentence_transformers import SentenceTransformer
        import torch
        
        self.embed_model = SentenceTransformer(model_name)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embed_model = self.embed_model.to(device)
        print(f"嵌入模型已加载: {model_name} on {device}")
    
    def retrieve(self, query, top_k=TOP_K):
        """检索相关chunks"""
        import numpy as np
        
        query_vec = self.embed_model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_vec.astype(np.float32), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score > 0.3:  # 相似度阈值
                results.append({
                    "chunk_id": self.chunk_mapping[idx]["chunk_id"],
                    "page_num": self.chunk_mapping[idx]["page_num"],
                    "text": self.chunk_mapping[idx]["text"],
                    "score": float(score)
                })
        
        return results
    
    def generate(self, query, context_chunks):
        """基于检索结果生成答案"""
        context = "\n\n".join([f"[第{c['page_num']}页] {c['text'][:1000]}" 
                              for c in context_chunks])
        
        prompt = f"""你是一个基于文档的问答助手。请根据以下文档内容回答问题。

文档内容：
{context}

问题：{query}

要求：
1. 仅基于提供的文档内容回答
2. 如果文档中没有相关信息，请明确说明
3. 引用信息来源（页码）
4. 回答简洁准确

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
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "生成失败")
            else:
                return f"LLM请求失败: {response.status_code}"
        except Exception as e:
            return f"LLM连接失败: {e}"
    
    def generate_direct_llm(self, query):
        """直接使用LLM回答（用于对比）"""
        prompt = f"""问题：{query}

请直接回答这个问题（不使用任何外部文档）。

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
        except:
            return "LLM不可用"
        return "LLM不可用"
    
    def answer(self, query):
        """完整的问答流程"""
        start = time.time()
        
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
            "retrieved_chunks": results,
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(gen_time, 3),
            "total_time": round(total_time, 3)
        }

def run_evaluation():
    """运行评估测试"""
    engine = RAGEngine()
    
    results = []
    for q in EVAL_QUESTIONS:
        print(f"\n{'='*60}")
        print(f"问题 [{q['id']}]: {q['question']}")
        
        # RAG回答
        rag_result = engine.answer(q["question"])
        print(f"RAG回答: {rag_result['answer'][:200]}")
        
        # 纯LLM回答
        llm_answer = engine.generate_direct_llm(q["question"])
        print(f"纯LLM: {llm_answer[:200]}")
        print(f"耗时: {rag_result['total_time']:.3f}s")
        
        results.append({
            "id": q["id"],
            "question": q["question"],
            "rag_answer": rag_result["answer"],
            "llm_answer": llm_answer,
            "retrieval_time": rag_result["retrieval_time"],
            "total_time": rag_result["total_time"],
            "retrieved_chunks": [{"chunk_id": c["chunk_id"], "score": c["score"]} 
                                 for c in rag_result["retrieved_chunks"]]
        })
    
    # 保存结果
    output_path = BASE_DIR / "logs" / "eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n评估结果已保存: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_evaluation()
    else:
        engine = RAGEngine()
        print("\nRAG问答引擎已启动 (输入 'exit' 退出)")
        while True:
            query = input("\n问题: ").strip()
            if query.lower() in ["exit", "quit", "q"]:
                break
            result = engine.answer(query)
            print(f"\n回答: {result['answer']}")
            print(f"检索耗时: {result['retrieval_time']}s | 生成耗时: {result['generation_time']}s | 总计: {result['total_time']}s")
            if result['retrieved_chunks']:
                print(f"引用来源: {', '.join([c['chunk_id'] for c in result['retrieved_chunks'][:3]])}")
