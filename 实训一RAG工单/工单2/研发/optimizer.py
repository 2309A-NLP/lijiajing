"""
工单02 - 优化模块
PDF解析优化 + 分块优化 + 检索优化
"""
import sys
import json
import time
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class PDFParserOptimizer:
    """PDF解析优化 - 比工单01更好的解析策略"""
    
    @staticmethod
    def extract_with_layout(pdf_path):
        """带布局信息的PDF提取，保留标题层级"""
        import pymupdf
        doc = pymupdf.open(pdf_path)
        pages = []
        
        for page_num, page in enumerate(doc, 1):
            # 获取文本块（带位置信息）
            blocks = page.get_text("dict")["blocks"]
            text_blocks = []
            
            for block in blocks:
                if block["type"] == 0:  # 文本块
                    text = ""
                    font_sizes = []
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text += span["text"]
                            font_sizes.append(span["size"])
                    
                    avg_font = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                    text_blocks.append({
                        "text": text,
                        "font_size": avg_font,
                        "bbox": block["bbox"],
                        "type": "heading" if avg_font > 14 else "body"
                    })
            
            pages.append({
                "page_num": page_num,
                "blocks": text_blocks
            })
        
        doc.close()
        return pages

class ChunkOptimizer:
    """分块优化 - 多种策略"""
    
    @staticmethod
    def semantic_chunking(pages, max_chars=512, overlap=64):
        """基于语义的分块（按标题分段）"""
        chunks = []
        
        for page in pages:
            current_section = []
            current_chars = 0
            
            for block in page["blocks"]:
                text = block["text"].strip()
                if not text:
                    continue
                
                # 如果是标题且当前区块已有内容，开始新chunk
                if block["type"] == "heading" and current_section:
                    chunk_text = "\n".join(current_section)
                    chunks.append({
                        "text": chunk_text,
                        "page_num": page["page_num"],
                        "char_count": len(chunk_text)
                    })
                    current_section = []
                    current_chars = 0
                
                current_section.append(text)
                current_chars += len(text)
                
                # 超过最大长度时切分
                if current_chars >= max_chars:
                    chunk_text = "\n".join(current_section)
                    chunks.append({
                        "text": chunk_text,
                        "page_num": page["page_num"],
                        "char_count": len(chunk_text)
                    })
                    current_section = [current_section[-1]] if current_section else []
                    current_chars = len(current_section[0]) if current_section else 0
            
            # 剩余内容
            if current_section:
                chunk_text = "\n".join(current_section)
                chunks.append({
                    "text": chunk_text,
                    "page_num": page["page_num"],
                    "char_count": len(chunk_text)
                })
        
        for i, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"opt_chunk_{i+1:04d}"
        
        return chunks
    
    @staticmethod
    def sliding_window_chunking(text, chunk_size=512, overlap=128):
        """滑动窗口分块"""
        import pymupdf
        chunks = []
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        buffer = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(buffer) + len(para) < chunk_size:
                buffer += para + "\n\n"
            else:
                if buffer:
                    chunks.append(buffer.strip())
                # 保留重叠部分
                buffer = buffer[-overlap:] + "\n\n" + para + "\n\n" if overlap > 0 else para + "\n\n"
        
        if buffer:
            chunks.append(buffer.strip())
        
        return chunks

class RetrievalOptimizer:
    """检索优化 - 多种检索策略"""
    
    @staticmethod
    def hybrid_search(query, vector_results, bm25_results, weights=(0.7, 0.3)):
        """混合检索：向量检索 + BM25关键词检索"""
        import numpy as np
        
        # 分数归一化
        all_chunks = {}
        
        max_vec_score = max([r["score"] for r in vector_results]) if vector_results else 1
        for r in vector_results:
            chunk_id = r["chunk_id"]
            all_chunks[chunk_id] = {
                "text": r["text"],
                "page_num": r["page_num"],
                "vec_score": r["score"] / max_vec_score,
                "bm25_score": 0
            }
        
        max_bm25_score = max([r["score"] for r in bm25_results]) if bm25_results else 1
        for r in bm25_results:
            chunk_id = r["chunk_id"]
            if chunk_id in all_chunks:
                all_chunks[chunk_id]["bm25_score"] = r["score"] / max_bm25_score
            else:
                all_chunks[chunk_id] = {
                    "text": r["text"],
                    "page_num": r["page_num"],
                    "vec_score": 0,
                    "bm25_score": r["score"] / max_bm25_score
                }
        
        # 加权融合
        result_list = []
        for chunk_id, data in all_chunks.items():
            hybrid_score = (weights[0] * data["vec_score"] + 
                          weights[1] * data["bm25_score"])
            result_list.append({
                "chunk_id": chunk_id,
                "text": data["text"],
                "page_num": data["page_num"],
                "score": hybrid_score,
                "vec_score": data["vec_score"],
                "bm25_score": data["bm25_score"]
            })
        
        result_list.sort(key=lambda x: x["score"], reverse=True)
        return result_list
    
    @staticmethod
    def query_expansion(query, llm_func=None):
        """查询扩展 - 生成同义查询"""
        if llm_func:
            prompt = f"""为以下问题生成3个同义改写版本，每个一行，不要序号：

问题：{query}

改写："""
            expanded = llm_func(prompt)
            queries = [q.strip() for q in expanded.strip().split('\n') if q.strip()]
            queries.insert(0, query)
            return queries
        return [query]

class Reranker:
    """重排序优化"""
    
    def __init__(self, model_name="BAAI/bge-reranker-base"):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.available = True
        except:
            print(f"重排序模型 {model_name} 不可用")
            self.available = False
    
    def rerank(self, query, candidates, top_k=5):
        if not self.available or not candidates:
            return candidates[:top_k]
        
        pairs = [[query, c["text"]] for c in candidates]
        scores = self.model.predict(pairs)
        
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        
        candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return candidates[:top_k]
