"""
工单03 - 表格解析模块
从PDF中提取表格数据，支持表格检索
"""
import sys
import json
import csv
import io
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class TableExtractor:
    """PDF表格提取器"""
    
    @staticmethod
    def extract_with_pymupdf(pdf_path):
        """使用PyMuPDF提取表格"""
        import pymupdf
        doc = pymupdf.open(pdf_path)
        tables = []
        
        for page_num, page in enumerate(doc, 1):
            # PyMuPDF的find_tables
            try:
                found = page.find_tables()
                if found and found.tables:
                    for table in found.tables:
                        rows = []
                        for row in table.extract():
                            clean_row = [str(cell).strip() if cell else "" for cell in row]
                            rows.append(clean_row)
                        
                        tables.append({
                            "page_num": page_num,
                            "bbox": list(table.bbox) if hasattr(table, 'bbox') else None,
                            "rows": rows,
                            "num_rows": len(rows),
                            "num_cols": len(rows[0]) if rows else 0
                        })
            except Exception as e:
                print(f"  第{page_num}页表格提取警告: {e}")
        
        doc.close()
        return tables
    
    @staticmethod
    def tables_to_text(tables):
        """将表格转为文本描述"""
        texts = []
        for i, table in enumerate(tables):
            lines = [f"[表格 {i+1} - 第{table['page_num']}页]"]
            
            if table["rows"]:
                header = " | ".join(table["rows"][0])
                lines.append(f"表头: {header}")
                lines.append(f"行数: {table['num_rows']-1} (不含表头)")
                
                # 所有行
                for row in table["rows"][1:]:
                    lines.append(" | ".join(row))
            
            texts.append("\n".join(lines))
        
        return "\n\n".join(texts)
    
    @staticmethod
    def tables_to_markdown(tables):
        """表格转Markdown格式"""
        md_parts = []
        for i, table in enumerate(tables):
            if not table["rows"]:
                continue
            
            md = [f"### 表格 {i+1} (第{table['page_num']}页)\n"]
            
            # 表头
            md.append("| " + " | ".join(table["rows"][0]) + " |")
            md.append("| " + " | ".join(["---"] * len(table["rows"][0])) + " |")
            
            # 数据行
            for row in table["rows"][1:]:
                md.append("| " + " | ".join(row) + " |")
            
            md_parts.append("\n".join(md))
        
        return "\n\n".join(md_parts)

class TableAwareRetriever:
    """表格感知检索器 - 将表格作为特殊chunk检索"""
    
    def __init__(self):
        self.table_chunks = []
    
    def prepare_table_chunks(self, tables):
        """将表格转换为可检索的chunks"""
        for i, table in enumerate(tables):
            if not table["rows"]:
                continue
            
            # 文本描述
            text_desc = TableExtractor.tables_to_text([table])
            
            # 关键词提取（从表头和首行数据）
            keywords = " ".join(table["rows"][0]) if table["rows"] else ""
            
            self.table_chunks.append({
                "chunk_id": f"table_{i+1:04d}",
                "page_num": table["page_num"],
                "text": text_desc,
                "markdown": TableExtractor.tables_to_markdown([table]),
                "keywords": keywords,
                "num_rows": table["num_rows"],
                "num_cols": table["num_cols"],
                "type": "table"
            })
        
        return self.table_chunks

if __name__ == "__main__":
    # 测试表格提取
    possible_paths = [
        "/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书1.pdf",
        "/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/招股说明书2.pdf",
    ]
    
    # 也试试新路径
    for pdf_name in ["招股说明书2.pdf", "招股说明书1.pdf"]:
        path = f"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/{pdf_name}"
        print(f"\n=== 解析 {pdf_name} ===")
        
        if not Path(path).exists():
            print(f"  文件不存在: {path}")
            continue
        
        extractor = TableExtractor()
        tables = extractor.extract_with_pymupdf(path)
        
        print(f"  找到 {len(tables)} 个表格")
        for t in tables:
            print(f"    第{t['page_num']}页: {t['num_rows']}行 x {t['num_cols']}列")
        
        if tables:
            print("\nMarkdown格式:")
            print(extractor.tables_to_markdown(tables)[:500])
        
        # 保存
        output = BASE_DIR / "knowledge_base" / f"tables_{pdf_name.replace('.pdf','')}.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(tables, f, ensure_ascii=False, indent=2)
        print(f"  已保存: {output}")
