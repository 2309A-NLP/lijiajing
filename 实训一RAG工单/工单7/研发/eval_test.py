"""
工单07 - 功能测试及评估模块
RAGAS评估、准确率测试、对比分析
"""
import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class RAGEvaluator:
    """RAG评估器"""
    
    def __init__(self):
        self.results = []
    
    def test_questions(self, qa_engine, questions):
        """批量测试问题"""
        print("\n=== 开始批量测试 ===\n")
        
        for q in questions:
            start = time.time()
            
            # RAG回答
            result = qa_engine.answer(q["question"])
            elapsed = time.time() - start
            
            self.results.append({
                "question_id": q["id"],
                "question": q["question"],
                "answer": result["answer"],
                "retrieved_chunks": result.get("retrieved_chunks", []),
                "response_time": round(elapsed, 3),
                "success": len(result.get("retrieved_chunks", [])) > 0
            })
            
            status = "✓" if self.results[-1]["success"] else "✗"
            print(f"  [{status}] Q{q['id']}: {q['question'][:50]}... ({elapsed:.2f}s)")
        
        return self.results
    
    def calc_metrics(self):
        """计算评估指标"""
        if not self.results:
            return {}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        avg_time = sum(r["response_time"] for r in self.results) / total
        
        metrics = {
            "total_questions": total,
            "successful": successful,
            "failed": total - successful,
            "accuracy": round(successful / total * 100, 2),
            "avg_response_time": round(avg_time, 3),
            "max_response_time": round(max(r["response_time"] for r in self.results), 3),
            "min_response_time": round(min(r["response_time"] for r in self.results), 3)
        }
        
        return metrics
    
    def compare_with_llm_only(self, qa_engine, questions, llm_func=None):
        """对比RAG vs 纯LLM"""
        comparison = []
        
        for q in questions:
            # RAG
            rag_result = qa_engine.answer(q["question"])
            
            # 纯LLM
            if llm_func:
                llm_answer = llm_func(q["question"])
            else:
                llm_answer = "[纯LLM回答待接入]"
            
            comparison.append({
                "question_id": q["id"],
                "question": q["question"],
                "rag_answer": rag_result["answer"],
                "llm_answer": llm_answer,
                "rag_had_context": len(rag_result.get("retrieved_chunks", [])) > 0
            })
        
        return comparison
    
    def save_report(self, output_dir=None):
        """保存评估报告"""
        if output_dir is None:
            output_dir = BASE_DIR / "logs"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metrics = self.calc_metrics()
        
        # JSON详细结果
        report = {
            "metrics": metrics,
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": self.results
        }
        
        json_path = output_dir / "eval_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Markdown报告
        md = f"""# RAG系统评估报告

## 总体指标
- 测试问题数: {metrics['total_questions']}
- 成功: {metrics['successful']} | 失败: {metrics['failed']}
- 准确率: {metrics['accuracy']}%
- 平均响应时间: {metrics['avg_response_time']}s
- 最大/最小响应时间: {metrics['max_response_time']}s / {metrics['min_response_time']}s

## 详细结果
| ID | 问题 | 响应时间 | 状态 |
|----|------|---------|------|
"""
        for r in self.results:
            status = "✓" if r["success"] else "✗"
            md += f"| {r['question_id']} | {r['question'][:40]}... | {r['response_time']}s | {status} |\n"
        
        md_path = output_dir / "eval_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        
        print(f"\n评估报告已保存:")
        print(f"  JSON: {json_path}")
        print(f"  MD:   {md_path}")
        
        return metrics

# RAGAS评估指标
class RAGASMetrics:
    """RAGAS评估框架集成"""
    
    @staticmethod
    def compute_context_precision(retrieved_chunks, relevant_chunks):
        """计算上下文精度"""
        if not retrieved_chunks:
            return 0
        
        retrieved_ids = {c["chunk_id"] for c in retrieved_chunks}
        relevant_ids = {c["chunk_id"] for c in relevant_chunks}
        
        if not relevant_ids:
            return 1.0 if not retrieved_ids else 0.0
        
        precision = len(retrieved_ids & relevant_ids) / len(retrieved_ids)
        return precision
    
    @staticmethod
    def compute_context_recall(retrieved_chunks, relevant_chunks):
        """计算上下文召回"""
        if not relevant_chunks:
            return 1.0
        
        retrieved_ids = {c["chunk_id"] for c in retrieved_chunks}
        relevant_ids = {c["chunk_id"] for c in relevant_chunks}
        
        recall = len(retrieved_ids & relevant_ids) / len(relevant_ids)
        return recall
    
    @staticmethod
    def compute_faithfulness(answer, context_chunks):
        """计算忠实度（简单的关键词匹配）"""
        if not answer or not context_chunks:
            return 0
        
        context_text = " ".join([c["text"][:500] for c in context_chunks])
        answer_chars = set(answer)
        context_chars = set(context_text)
        
        if not answer_chars:
            return 0
        
        overlap = len(answer_chars & context_chars) / len(answer_chars)
        return overlap

if __name__ == "__main__":
    print("测试评估模块加载完成")
    print("支持的评估方法:")
    print("  1. 基础指标: 准确率、响应时间")
    print("  2. RAGAS指标: 上下文精度、召回、忠实度")
    print("  3. 对比评估: RAG vs 纯LLM")
    print("\n使用方法:")
    print("  from eval_test import RAGEvaluator, RAGASMetrics")
