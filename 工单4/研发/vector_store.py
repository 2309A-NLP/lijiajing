"""
工单01 - 向量库构建模块
将文本chunks向量化并存入向量数据库
"""
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from config import EMBED_MODEL, VECTOR_DB_PATH, KB_DIR, CHUNK_SIZE

def load_chunks():
    """加载已解析的chunks"""
    chunks_path = KB_DIR / "chunks.json"
    if not chunks_path.exists():
        print("ERROR: 请先运行 pdf_parser.py")
        return None
    with open(chunks_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_embeddings(chunks, model_name=EMBED_MODEL):
    """使用sentence-transformers生成embeddings"""
    from sentence_transformers import SentenceTransformer
    
    print(f"加载嵌入模型: {model_name}")
    start = time.time()
    model = SentenceTransformer(model_name)
    print(f"  模型加载耗时: {time.time()-start:.2f}s")
    
    # 检查CUDA
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  使用设备: {device}")
    model = model.to(device)
    
    texts = [chunk["text"] for chunk in chunks]
    
    print(f"生成embeddings: {len(texts)}个chunks...")
    start = time.time()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    print(f"  耗时: {time.time()-start:.2f}s")
    print(f"  维度: {embeddings.shape}")
    
    return model, embeddings

def store_faiss(embeddings, chunks):
    """使用FAISS存储向量"""
    import faiss
    import numpy as np
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # 内积=余弦相似度（归一化后）
    index.add(embeddings.astype(np.float32))
    
    # 保存索引
    index_path = VECTOR_DB_PATH / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    
    # 保存chunks映射
    mapping_path = VECTOR_DB_PATH / "chunk_mapping.json"
    mapping = [{"chunk_id": c["chunk_id"], "page_num": c["page_num"], "text": c["text"]} 
               for c in chunks]
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"FAISS索引已保存: {index_path}")
    print(f"  chunks: {len(mapping)}")
    print(f"  维度: {dim}")
    return index_path

def build_milvus(embeddings, chunks):
    """使用Milvus Lite存储向量（备用方案）"""
    try:
        from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
        
        # 连接Milvus
        connections.connect(host="localhost", port="19530")
        
        collection_name = "rag_workorder_01"
        
        # 如果已存在则删除重建
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
        
        # 定义schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="page_num", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embeddings.shape[1]),
        ]
        schema = CollectionSchema(fields)
        collection = Collection(name=collection_name, schema=schema)
        
        # 插入数据
        import numpy as np
        data = [
            [c["chunk_id"] for c in chunks],
            [c["page_num"] for c in chunks],
            [c["text"] for c in chunks],
            embeddings.tolist()
        ]
        collection.insert(data)
        collection.flush()
        
        # 创建索引
        index_params = {
            "metric_type": "IP",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)
        collection.load()
        
        print(f"Milvus集合已创建: {collection_name}")
        print(f"  数据量: {collection.num_entities}")
        
        return collection_name
    except Exception as e:
        print(f"Milvus不可用，已使用FAISS: {e}")
        return None

if __name__ == "__main__":
    chunks = load_chunks()
    if not chunks:
        sys.exit(1)
    
    model, embeddings = build_embeddings(chunks)
    
    # 主方案：FAISS
    store_faiss(embeddings, chunks)
    
    # 备选方案：如果Milvus可用
    build_milvus(embeddings, chunks)
    
    print("向量库构建完成！")
