"""
工单02 - 优化前后对比测试
"""
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from optimizer import PDFParserOptimizer, ChunkOptimizer

def compare_parsing(pdf_path):
    """对比原始解析和优化解析"""
    import pymupdf
    
    # 原始方式
    start = time.time()
    doc = pymupdf.open(pdf_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    doc.close()
    raw_time = time.time() - start
    
    # 优化方式
    start = time.time()
    optimizer = PDFParserOptimizer()
    pages = optimizer.extract_with_layout(pdf_path)
    opt_time = time.time() - start
    
    # 统计
    total_blocks = sum(len(p["blocks"]) for p in pages)
    headings = sum(1 for p in pages for b in p["blocks"] if b["type"] == "heading")
    
    print(f"原始解析: {len(raw_text)}字符, {raw_time:.2f}s")
    print(f"优化解析: {total_blocks}个文本块 (含{headings}个标题), {opt_time:.2f}s")
    
    return {"raw_chars": len(raw_text), "optimized_blocks": total_blocks, "headings": headings}

def compare_chunking(chunks_original, chunks_optimized):
    """对比分块效果"""
    print(f"\n原始分块: {len(chunks_original)}个chunks")
    print(f"优化分块: {len(chunks_optimized)}个chunks")
    
    # 分析chunk质量
    orig_avg = sum(c["char_count"] for c in chunks_original) / len(chunks_original)
    opt_avg = sum(c["char_count"] for c in chunks_optimized) / len(chunks_optimized)
    
    print(f"原始平均长度: {orig_avg:.0f}字符")
    print(f"优化平均长度: {opt_avg:.0f}字符")
    
    return {"original_count": len(chunks_original), "optimized_count": len(chunks_optimized)}

if __name__ == "__main__":
    # 找到PDF
    possible_paths = [
        "/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书1.pdf",
        "/mnt/d/2309A nlp 上课软件/招股说明书/招股说明书1.pdf",
    ]
    
    pdf_path = None
    for p in possible_paths:
        if Path(p).exists():
            pdf_path = p
            break
    
    if not pdf_path:
        print("ERROR: 找不到招股说明书PDF")
        sys.exit(1)
    
    print(f"PDF路径: {pdf_path}")
    
    # 对比解析
    print("\n=== PDF解析对比 ===")
    compare_parsing(pdf_path)
    
    # 对比分块
    print("\n=== 分块策略对比 ===")
    optimizer = PDFParserOptimizer()
    pages = optimizer.extract_with_layout(pdf_path)
    chunk_opt = ChunkOptimizer()
    optimized = chunk_opt.semantic_chunking(pages)
    
    print(f"语义分块: {len(optimized)}个chunks")
    
    # 保存优化结果
    output_path = BASE_DIR / "knowledge_base" / "optimized_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(optimized, f, ensure_ascii=False, indent=2)
    
    print(f"优化结果已保存: {output_path}")
    print("\n=== 优化完成 ===")
