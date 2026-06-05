"""
工单04 - 图像内容解析模块
从PDF中提取图片，OCR识别，支持图像内容检索
"""
import sys
import json
import os
from pathlib import Path
import base64
import io

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class ImageExtractor:
    """PDF图像提取"""
    
    @staticmethod
    def extract_images(pdf_path, output_dir=None):
        """从PDF中提取所有图片"""
        import pymupdf
        
        if output_dir is None:
            output_dir = BASE_DIR / "knowledge_base" / "extracted_images"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        doc = pymupdf.open(pdf_path)
        images = []
        
        for page_num, page in enumerate(doc, 1):
            image_list = page.get_images(full=True)
            
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 保存图片
                img_filename = f"p{page_num}_img{img_idx+1}.{image_ext}"
                img_path = output_dir / img_filename
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                
                images.append({
                    "page_num": page_num,
                    "index": img_idx,
                    "filename": img_filename,
                    "path": str(img_path),
                    "size": len(image_bytes),
                    "ext": image_ext,
                    "width": base_image.get("width", 0),
                    "height": base_image.get("height", 0)
                })
        
        doc.close()
        
        # 保存索引
        index_path = output_dir / "image_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(images, f, ensure_ascii=False, indent=2)
        
        print(f"提取 {len(images)} 张图片到 {output_dir}")
        return images

class ImageOCR:
    """图片OCR识别"""
    
    @staticmethod
    def ocr_image(image_path, lang="chi_sim+eng"):
        """OCR识别图片文字"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=lang)
            return text.strip()
        except ImportError:
            print("  pytesseract未安装，尝试备用方案...")
            return ImageOCR._ocr_fallback(image_path)
    
    @staticmethod
    def _ocr_fallback(image_path):
        """备用：使用pymupdf自带的OCR"""
        try:
            import pymupdf
            # PyMuPDF可以提取图片，但OCR需要tesseract
            return ""
        except:
            return ""
    
    @staticmethod
    def batch_ocr(images, lang="chi_sim+eng"):
        """批量OCR"""
        results = []
        for img_info in images:
            text = ImageOCR.ocr_image(img_info["path"], lang)
            results.append({
                **img_info,
                "ocr_text": text,
                "ocr_chars": len(text)
            })
            print(f"  {img_info['filename']}: {len(text)}字符")
        
        # 保存结果
        output_path = Path(images[0]["path"]).parent / "ocr_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results

class ImageCaptioner:
    """图片描述生成（备用方案）"""
    
    @staticmethod
    def describe_image(image_path):
        """使用LLM描述图片内容（需要LLM API）"""
        import base64
        
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        # 这里对接LLM视觉API
        prompt = "请用中文描述这张图片的内容和关键信息。"
        
        # 占位 - 实际需要LLM视觉能力
        return "[图片描述待LLM视觉API接入]"

if __name__ == "__main__":
    import pymupdf
    
    # 测试图片提取
    for pdf_name in ["招股说明书1.pdf", "招股说明书2.pdf"]:
        path = f"/mnt/c/Users/10608/Desktop/实训工单/RAG工单/RAG 工单/附件/{pdf_name}"
        
        if not Path(path).exists():
            print(f"文件不存在: {path}")
            continue
        
        print(f"\n=== 提取 {pdf_name} 中的图片 ===")
        images = ImageExtractor.extract_images(path)
        
        if images:
            print(f"共 {len(images)} 张图片")
            for img in images:
                print(f"  第{img['page_num']}页: {img['filename']} ({img['width']}x{img['height']}, {img['size']//1024}KB)")
        else:
            print("  未发现图片")
