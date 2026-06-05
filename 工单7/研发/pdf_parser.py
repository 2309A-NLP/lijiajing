"""
工单07 - PDF解析模块（CCF竞赛数据）
处理9份金融年报PDF
"""
import sys, os, json, hashlib, glob
from pathlib import Path

BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "knowledge_base"
DATA_DIR = BASE_DIR / "data"

def find_ccf_pdfs():
    """查找CCF竞赛的PDF文件"""
    ccf_dirs = [
        DATA_DIR / "ccf" / "ccf_competition" / "pdf",
        DATA_DIR / "ccf",
    ]
    for d in ccf_dirs:
        if d.exists():
            pdfs = sorted(d.glob("*.pdf"))
            if pdfs:
                return pdfs, d
    return [], None

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
            "char_count": len(text),
            "source_pdf": pdf_path.name,
        })
    doc.close()
    print(f"  ✅ {pdf_path.name}: {len(pages_text)}页")
    return pages_text

def chunk_text(pages_text, chunk_size=512, overlap=64):
    """将文本分割为chunks"""
    chunks = []
    for page in pages_text:
        text = page["text"]
        if not text.strip():
            continue
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
                        "page_num": page["page_num"],
                        "text": current_chunk.strip(),
                        "char_count": len(current_chunk),
                        "source_pdf": page.get("source_pdf", ""),
                    })
                current_chunk = para + "\n"
        if current_chunk:
            chunks.append({
                "page_num": page["page_num"],
                "text": current_chunk.strip(),
                "char_count": len(current_chunk),
                "source_pdf": page.get("source_pdf", ""),
            })
    
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = f"ccf_chunk_{i+1:05d}"
        chunk["doc_id"] = hashlib.md5(chunk["text"].encode()).hexdigest()[:12]
    
    return chunks

def save_chunks(chunks, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"\nChunks saved: {len(chunks)} chunks → {output_path}")
    # 统计各PDF来源
    from collections import Counter
    sources = Counter(c.get("source_pdf", "unknown") for c in chunks)
    print("各PDF贡献chunks:")
    for src, cnt in sources.most_common():
        print(f"  {src}: {cnt} chunks")

if __name__ == "__main__":
    pdfs, pdf_dir = find_ccf_pdfs()
    if not pdfs:
        print("ERROR: 找不到CCF竞赛PDF文件！")
        print(f"请检查: {DATA_DIR}/ccf/ 目录")
        sys.exit(1)
    
    print(f"找到 {len(pdfs)} 份CCF金融年报PDF:")
    all_pages = []
    for pdf_path in pdfs:
        try:
            pages = extract_text_from_pdf(pdf_path)
            all_pages.extend(pages)
        except Exception as e:
            print(f"  ❌ {pdf_path.name}: 解析失败 - {e}")
    
    print(f"\n总页数: {len(all_pages)}")
    
    chunks = chunk_text(all_pages)
    print(f"总chunks: {len(chunks)}")
    
    save_chunks(chunks, KB_DIR)
    print("\nCCF PDF解析完成！")
