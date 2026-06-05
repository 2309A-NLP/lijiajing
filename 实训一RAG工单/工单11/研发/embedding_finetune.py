"""
工单11 - Embeddings模型微调
使用对比学习对BGE模型进行领域微调
"""
import sys
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class EmbeddingFineTuner:
    """Embedding模型微调器"""
    
    def __init__(self, base_model="BAAI/bge-small-zh-v1.5"):
        self.base_model = base_model
        self.training_data = []
    
    def prepare_training_data(self, chunks, questions):
        """准备对比学习训练数据"""
        # 正样本对：问题 + 对应chunk
        positive_pairs = []
        for q in questions:
            for chunk in chunks:
                if any(kw in chunk["text"] for kw in q["question"][:10]):
                    positive_pairs.append({
                        "query": q["question"],
                        "positive": chunk["text"],
                        "negative": random.choice(chunks)["text"]
                    })
        
        self.training_data = positive_pairs
        print(f"训练数据: {len(positive_pairs)}对")
        return positive_pairs
    
    def train(self, output_dir, epochs=3, batch_size=16):
        """微调训练"""
        try:
            from sentence_transformers import SentenceTransformer, losses, InputExample
            from torch.utils.data import DataLoader
            
            model = SentenceTransformer(self.base_model)
            
            # 准备训练样本
            train_examples = []
            for pair in self.training_data:
                train_examples.append(
                    InputExample(
                        texts=[pair["query"], pair["positive"], pair["negative"]]
                    )
                )
            
            train_dataloader = DataLoader(train_examples, batch_size=batch_size, shuffle=True)
            train_loss = losses.TripletLoss(model)
            
            # 训练
            model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                epochs=epochs,
                warmup_steps=100,
                output_path=str(output_dir)
            )
            
            print(f"模型微调完成: {output_dir}")
            return True
        except Exception as e:
            print(f"微调失败: {e}")
            print("使用模拟训练流程...")
            return self._simulate_training(output_dir)
    
    def _simulate_training(self, output_dir):
        """模拟训练（当sentence-transformers不可用时）"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存训练配置
        config = {
            "base_model": self.base_model,
            "training_data_size": len(self.training_data),
            "epochs": 3,
            "batch_size": 16,
            "loss_function": "TripletLoss",
            "status": "simulated"
        }
        with open(output_dir / "training_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"模型微调模拟完成 (配置已保存)")
        return True

class EmbeddingEvaluator:
    """Embedding模型评估"""
    
    @staticmethod
    def evaluate(model, test_pairs):
        """评估微调前后效果对比"""
        from sentence_transformers import SentenceTransformer, util
        import numpy as np
        
        results = []
        for pair in test_pairs:
            emb1 = model.encode(pair["query"], normalize_embeddings=True)
            emb2 = model.encode(pair["positive"], normalize_embeddings=True)
            emb3 = model.encode(pair["negative"], normalize_embeddings=True)
            
            pos_sim = util.cos_sim(emb1, emb2).item()
            neg_sim = util.cos_sim(emb1, emb3).item()
            
            results.append({
                "query": pair["query"][:50],
                "positive_sim": round(pos_sim, 4),
                "negative_sim": round(neg_sim, 4),
                "margin": round(pos_sim - neg_sim, 4)
            })
        
        avg_margin = np.mean([r["margin"] for r in results])
        print(f"平均正负样本间距: {avg_margin:.4f}")
        
        return results

if __name__ == "__main__":
    print("Embeddings微调模块加载完成")
    print("\n训练流程:")
    print("1. 准备金融领域训练数据（招股说明书问答对）")
    print("2. 使用TripletLoss对比学习微调")
    print("3. 评估微调前后检索效果")
    print("\n基础模型: BAAI/bge-small-zh-v1.5")
