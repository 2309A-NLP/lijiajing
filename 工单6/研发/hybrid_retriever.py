"""
工单06 - 混合检索模块（中英双语）
向量检索(FAISS) + 全文检索(BM25) + 混合检索(加权融合)
支持中文和英文问答，3种重排算法

工单编号：人工智能NLP-RAG-混合检索任务
"""
import sys
import json
import re
import math
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


def detect_language(text):
    """检测查询语言：zh=中文, en=英文, mixed=中英混合"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    if chinese_chars > 0 and english_words == 0:
        return "zh"
    elif english_words > 0 and chinese_chars == 0:
        return "en"
    elif chinese_chars > 0 and english_words > 0:
        return "mixed"
    else:
        return "unknown"


def tokenize_multilingual(text):
    """
    中英双语分词
    - 中文：按字符级2-gram + 词组分词
    - 英文：按空格分词，小写化，去标点
    - 混合：同时处理中英文
    """
    tokens = []
    
    # 英文单词（包括数字）
    eng_tokens = re.findall(r'[a-zA-Z0-9]+', text)
    tokens.extend([t.lower() for t in eng_tokens])
    
    # 中文单字
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    tokens.extend(chinese_chars)
    
    # 中文2-gram
    if len(chinese_chars) >= 2:
        bigrams = [chinese_chars[i] + chinese_chars[i+1] 
                   for i in range(len(chinese_chars)-1)]
        tokens.extend(bigrams)
    
    # 中文常见词组（2-4字组合）
    if len(chinese_chars) >= 2:
        phrases = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
        tokens.extend(phrases)
    
    return list(set(tokens))  # 去重


class BM25Retriever:
    """BM25全文检索器（中英双语）"""
    
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.chunks = []
        self.doc_freqs = {}
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.num_docs = 0
        self.doc_tokens_cache = []  # 缓存已分词的文档
    
    def fit(self, chunks):
        """训练BM25模型"""
        self.chunks = chunks
        self.num_docs = len(chunks)
        self.doc_tokens_cache = []
        
        for i, chunk in enumerate(chunks):
            tokens = tokenize_multilingual(chunk["text"])
            self.doc_tokens_cache.append(tokens)
            self.doc_lengths.append(len(tokens))
            
            seen = set()
            for token in tokens:
                if token not in seen:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                    seen.add(token)
        
        self.avg_doc_length = np.mean(self.doc_lengths) if self.doc_lengths else 1
        print(f"BM25训练完成: {self.num_docs}文档, {len(self.doc_freqs)}个词汇")
    
    def get_scores(self, query_tokens):
        """计算BM25分数"""
        scores = np.zeros(self.num_docs)
        
        for token in query_tokens:
            if token not in self.doc_freqs:
                continue
            
            df = self.doc_freqs[token]
            idf = np.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)
            
            for i in range(self.num_docs):
                tf = self.doc_tokens_cache[i].count(token)
                
                if tf > 0:
                    score = idf * ((tf * (self.k1 + 1)) / 
                                  (tf + self.k1 * (1 - self.b + self.b * 
                                   self.doc_lengths[i] / self.avg_doc_length)))
                    scores[i] += score
        
        return scores
    
    def search(self, query, top_k=10):
        """执行全文检索"""
        tokens = tokenize_multilingual(query)
        scores = self.get_scores(tokens)
        
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "chunk_id": self.chunks[idx]["chunk_id"],
                    "text": self.chunks[idx]["text"][:500],
                    "page_num": self.chunks[idx]["page_num"],
                    "score": float(scores[idx]),
                    "method": "fulltext"
                })
        return results


class HybridRetriever:
    """混合检索器（向量 + 全文检索，中英双语）"""
    
    def __init__(self):
        self.vector_index = None
        self.chunk_mapping = None
        self.bm25 = None
        self.embed_model = None
        self.vector_weight = 0.6
        self.keyword_weight = 0.4
    
    def set_weights(self, vec_weight=0.6, kw_weight=0.4):
        self.vector_weight = vec_weight
        self.keyword_weight = kw_weight
    
    def load_vector_store(self, vector_db_path):
        """加载FAISS向量库"""
        import faiss
        
        index_path = vector_db_path / "faiss_index.bin"
        mapping_path = vector_db_path / "chunk_mapping.json"
        
        self.vector_index = faiss.read_index(str(index_path))
        with open(mapping_path, "r", encoding="utf-8") as f:
            self.chunk_mapping = json.load(f)
        
        print(f"向量库已加载: {self.vector_index.ntotal}个向量, 维度{self.vector_index.d}")
    
    def load_embedding_model(self, model_name="BAAI/bge-small-zh-v1.5"):
        """加载嵌入模型（使用 transformers 替代 sentence-transformers）"""
        from transformers import AutoTokenizer, AutoModel
        import torch
        
        self.embed_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.embed_model = AutoModel.from_pretrained(model_name)
        self.embed_model.eval()
        
        self.embed_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embed_model = self.embed_model.to(self.embed_device)
        print(f"嵌入模型已加载: {model_name} on {self.embed_device}")
    
    def init_bm25(self, chunks):
        """初始化BM25全文检索"""
        # 从chunk_mapping构建chunks列表
        chunk_list = []
        for idx_str, mapping in enumerate(self.chunk_mapping):
            # chunk_mapping可能是list或dict
            if isinstance(self.chunk_mapping, list):
                item = self.chunk_mapping[idx_str]
            else:
                item = mapping
            chunk_list.append({
                "chunk_id": item.get("chunk_id", str(idx_str)),
                "text": item.get("text", ""),
                "page_num": item.get("page_num", 0),
            })
        
        self.bm25 = BM25Retriever()
        self.bm25.fit(chunk_list)
    
    def vector_search(self, query, top_k=10):
        """向量检索（中英双语兼容）"""
        if not self.vector_index or not self.embed_model:
            return []
        
        import numpy as np
        import torch
        
        # 使用 transformers 编码
        inputs = self.embed_tokenizer([query], padding=True, truncation=True,
                                       return_tensors='pt', max_length=512)
        inputs = {k: v.to(self.embed_device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.embed_model(**inputs)
        query_vec = outputs.last_hidden_state.mean(dim=1)
        query_vec = torch.nn.functional.normalize(query_vec, p=2, dim=1)
        query_vec = query_vec.cpu().numpy().astype(np.float32)
        scores, indices = self.vector_index.search(query_vec.astype(np.float32), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score > 0.3:
                mapping = self.chunk_mapping[idx] if isinstance(self.chunk_mapping, list) else self.chunk_mapping[idx] 
                results.append({
                    "chunk_id": mapping.get("chunk_id", str(idx)),
                    "text": mapping.get("text", "")[:500],
                    "page_num": mapping.get("page_num", 0),
                    "score": float(score),
                    "method": "vector"
                })
        return results
    
    def keyword_search(self, query, top_k=10):
        """关键词全文检索（中英双语）"""
        if not self.bm25:
            return []
        return self.bm25.search(query, top_k)
    
    def rerank_tfidf(self, results, query):
        """重排算法1：基于TF-IDF的相关性重排"""
        if not results:
            return results
        
        query_tokens = tokenize_multilingual(query)
        for r in results:
            doc_tokens = tokenize_multilingual(r["text"][:1000])
            overlap = len(set(query_tokens) & set(doc_tokens))
            r["rerank_score"] = r["score"] * (1 + 0.2 * overlap / max(len(query_tokens), 1))
        
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results
    
    def rerank_position(self, results):
        """重排算法2：基于位置的重排（靠前的结果加分）"""
        for i, r in enumerate(results):
            position_boost = 1.0 - 0.1 * i  # 越靠前加分越多
            r["rerank_score"] = r.get("rerank_score", r["score"]) * position_boost
        
        return results
    
    def rerank_diversity(self, results):
        """重排算法3：基于内容多样性的重排（避免重复内容）"""
        if not results:
            return results
        
        diversified = []
        seen_texts = []
        
        for r in results:
            is_duplicate = False
            for seen in seen_texts:
                # 简单的内容重叠检测
                overlap = len(set(r["text"][:200]) & set(seen[:200])) / max(len(set(r["text"][:200]) | set(seen[:200])), 1)
                if overlap > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                diversified.append(r)
                seen_texts.append(r["text"][:200])
        
        return diversified
    
    def hybrid_search(self, query, top_k=5, rerank_methods=None):
        """
        混合检索（向量 + 全文检索）
        
        参数:
            query: 查询文本（中/英/混合）
            top_k: 返回结果数
            rerank_methods: 重排方法列表，如 ["tfidf", "position", "diversity"]
        """
        lang = detect_language(query)
        print(f"  检测语言: {lang}, 查询: {query[:60]}...")
        
        # 并行检索
        vec_results = self.vector_search(query, top_k * 3)
        kw_results = self.keyword_search(query, top_k * 3)
        
        # 分数归一化 + 融合
        all_results = {}
        
        max_vec = max([r["score"] for r in vec_results]) if vec_results else 1
        for r in vec_results:
            all_results[r["chunk_id"]] = {
                "text": r["text"],
                "page_num": r["page_num"],
                "vec_score": r["score"] / max_vec,
                "kw_score": 0,
                "methods": ["vector"]
            }
        
        max_kw = max([r["score"] for r in kw_results]) if kw_results else 1
        for r in kw_results:
            if r["chunk_id"] in all_results:
                all_results[r["chunk_id"]]["kw_score"] = r["score"] / max_kw
                all_results[r["chunk_id"]]["methods"].append("fulltext")
            else:
                all_results[r["chunk_id"]] = {
                    "text": r["text"],
                    "page_num": r["page_num"],
                    "vec_score": 0,
                    "kw_score": r["score"] / max_kw,
                    "methods": ["fulltext"]
                }
        
        # 加权融合
        final = []
        for chunk_id, data in all_results.items():
            hybrid = (self.vector_weight * data["vec_score"] + 
                     self.keyword_weight * data["kw_score"])
            final.append({
                "chunk_id": chunk_id,
                "text": data["text"],
                "page_num": data["page_num"],
                "score": hybrid,
                "methods": data["methods"]
            })
        
        # 重排
        if rerank_methods:
            for method in rerank_methods:
                if method == "tfidf":
                    final = self.rerank_tfidf(final, query)
                elif method == "position":
                    final = self.rerank_position(final)
                elif method == "diversity":
                    final = self.rerank_diversity(final)
        
        final.sort(key=lambda x: x["score"], reverse=True)
        return final[:top_k]
    
    def fulltext_only(self, query, top_k=5):
        """仅全文检索（中英双语）"""
        return self.keyword_search(query, top_k)
    
    def vector_only(self, query, top_k=5):
        """仅向量检索（中英双语）"""
        return self.vector_search(query, top_k)


if __name__ == "__main__":
    print("=" * 60)
    print("工单06 - 混合检索模块（中英双语）")
    print("=" * 60)
    print("\n支持的检索方式:")
    print("  1. 向量检索 (embedding similarity)")
    print("  2. BM25关键词全文检索 (中英双语)")
    print("  3. 混合检索 (加权融合)")
    print("\n中英双语分词测试:")
    tests = [
        "报告期内，武汉兴图新科电子股份有限公司来自军用领域的收入分别是多少？",
        "What is the registered capital of Wuhan Xingtu Xinke?",
        "Who is the legal representative of 力源信息?",
    ]
    for t in tests:
        lang = detect_language(t)
        tokens = tokenize_multilingual(t)
        print(f"  [{lang}] {t[:40]}... -> {len(tokens)}个词元")
    
    retriever = HybridRetriever()
    retriever.set_weights(0.6, 0.4)
    print(f"\n  向量权重: {retriever.vector_weight}")
    print(f"  关键词权重: {retriever.keyword_weight}")
