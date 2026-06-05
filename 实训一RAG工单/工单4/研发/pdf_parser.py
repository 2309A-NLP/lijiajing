"""
工单03 - PDF解析模块（支持多PDF）
基于PyMuPDF解析多个招股说明书PDF，提取文本内容并分块
工单03需要解析：招股说明书1.pdf + 招股说明书2.pdf
"""
import sys
import os
from pathlib import Path
import json
import hashlib

# 配置
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
try:
    from config import PDF_PATHS, PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP, KB_DIR
except ImportError:
    from config import PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP, KB_DIR
    PDF_PATHS = [PDF_PATH]

def extract_text_from_pdf(pdf_path, pdf_label=""):
    """使用PyMuPDF提取PDF文本"""
    import pymupdf
    print(f"  解析: {pdf_label or os.path.basename(pdf_path)}")
    doc = pymupdf.open(pdf_path)
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages_text.append({
            "page_num": i + 1,
            "text": text,
            "char_count": len(text),
            "source_pdf": pdf_label or os.path.basename(pdf_path),
        })
    doc.close()
    return pages_text, doc.metadata

def extract_text_from_pdfs(pdf_paths):
    """从多个PDF提取文本"""
    all_pages = []
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            pages, _ = extract_text_from_pdf(pdf_path)
            all_pages.extend(pages)
        else:
            print(f"  ⚠️ PDF不存在: {pdf_path}")
    return all_pages

def chunk_text(pages_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """将文本分割为重叠的chunks"""
    chunks = []
    for page in pages_text:
        text = page["text"]
        page_num = page["page_num"]
        source_pdf = page.get("source_pdf", "")
        
        if not text.strip():
            continue
        
        # 按段落分割
        paragraphs = text.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n"
            else:
                if current_chunk:
                    chunks.append({
                        "page_num": page_num,
                        "text": current_chunk.strip(),
                        "char_count": len(current_chunk),
                        "source_pdf": source_pdf,
                    })
                current_chunk = para + "\n"
        
        if current_chunk:
            chunks.append({
                "page_num": page_num,
                "text": current_chunk.strip(),
                "char_count": len(current_chunk),
                "source_pdf": source_pdf,
            })
    
    # 添加chunk_id
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = f"chunk_{i+1:04d}"
        chunk["doc_id"] = hashlib.md5(chunk["text"].encode()).hexdigest()[:12]
    
    return chunks

def save_chunks(chunks, output_dir):
    """保存chunks到JSON文件"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    # 预览
    txt_path = output_dir / "chunks_preview.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for chunk in chunks[:5]:
            src = chunk.get("source_pdf", "")
            f.write(f"=== {chunk['chunk_id']} (Page {chunk['page_num']}, {src}) ===\n")
            f.write(chunk["text"][:300])
            f.write("\n...\n\n")
    
    print(f"  Chunks saved: {len(chunks)} chunks → {output_path}")
    return output_path

if __name__ == "__main__":
    # 尝试多个可能的PDF路径
    possible_paths = PDF_PATHS + [
        str(BASE_DIR / "../附件/招股说明书1.pdf"),
        str(BASE_DIR / "../附件/招股说明书2.pdf"),
        "/mnt/d/2309A nlp 上课软件/招股说明书/招股说明书1.pdf",
        "/mnt/d/2309A nlp 上课软件/招股说明书/招股说明书2.pdf",
    ]
    
    found_paths = []
    for p in set(possible_paths):
        if os.path.exists(p) and p not in found_paths:
            found_paths.append(p)
    
    if not found_paths:
        print("ERROR: 找不到PDF文件！")
        print("请检查以下路径：")
        for p in set(possible_paths):
            print(f"  - {p}")
        sys.exit(1)
    
    print(f"解析 {len(found_paths)} 个PDF文件:")
    pages_text = extract_text_from_pdfs(found_paths)
    print(f"  总页数: {len(pages_text)}")
    
    chunks = chunk_text(pages_text)
    print(f"  总chunks: {len(chunks)}")
    
    save_path = save_chunks(chunks, KB_DIR)
    print("PDF解析完成！")
