"""
工单01 - PDF解析模块
基于PyMuPDF解析招股说明书，提取文本内容并分块
"""
import sys
import os
from pathlib import Path
import json
import hashlib

# 配置
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from config import PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP, KB_DIR

def extract_text_from_pdf(pdf_path):
    """使用PyMuPDF提取PDF文本"""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages_text.append({
            "page_num": i + 1,
            "text": text,
            "char_count": len(text)
        })
    doc.close()
    return pages_text, doc.metadata

def chunk_text(pages_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """将文本分割为重叠的chunks"""
    chunks = []
    for page in pages_text:
        text = page["text"]
        page_num = page["page_num"]
        
        if not text.strip():
            continue
        
        # 按段落分割
        paragraphs = text.split("\n\n")
        current_chunk = ""
        current_start = 0
        
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
                    })
                current_chunk = para + "\n"
        
        if current_chunk:
            chunks.append({
                "page_num": page_num,
                "text": current_chunk.strip(),
                "char_count": len(current_chunk),
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
    
    # 也保存为纯文本方便查看
    txt_path = output_dir / "chunks_preview.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for chunk in chunks[:5]:  # 预览前5个
            f.write(f"=== {chunk['chunk_id']} (Page {chunk['page_num']}) ===\n")
            f.write(chunk["text"][:300])
            f.write("\n...\n\n")
    
    print(f"Chunks saved: {len(chunks)} chunks → {output_path}")
    print(f"Preview saved: {txt_path}")
    return output_path

if __name__ == "__main__":
    # 尝试多个可能的PDF路径
    possible_paths = [
        PDF_PATH,
        str(BASE_DIR / "../附件/招股说明书1.pdf"),
        "/mnt/d/2309A nlp 上课软件/招股说明书/招股说明书1.pdf",
        "/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书1.pdf",
    ]
    
    pdf_found = None
    for p in possible_paths:
        if os.path.exists(p):
            pdf_found = p
            break
    
    if not pdf_found:
        print("ERROR: 找不到招股说明书PDF！")
        print("请检查以下路径之一：")
        for p in possible_paths:
            print(f"  - {p}")
        sys.exit(1)
    
    print(f"解析PDF: {pdf_found}")
    pages_text, metadata = extract_text_from_pdf(pdf_found)
    print(f"  页数: {len(pages_text)}")
    print(f"  元数据: {metadata['title']}, {metadata['author']}")
    
    chunks = chunk_text(pages_text)
    print(f"  分块数: {len(chunks)}")
    
    save_path = save_chunks(chunks, KB_DIR)
    print("PDF解析完成！")
