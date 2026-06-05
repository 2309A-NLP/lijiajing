"""
工单13 - RAG性能瓶颈识别与优化
性能分析、瓶颈诊断、优化方案
"""
import sys
import json
import time
import cProfile
import io
import pstats
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics = {
            "pdf_parse_time": [],
            "chunk_time": [],
            "embed_time": [],
            "retrieval_time": [],
            "generation_time": [],
            "total_time": []
        }
    
    def profile_pipeline(self, pipeline_func, *args, **kwargs):
        """分析完整pipeline各阶段耗时"""
        stages = {}
        
        # 使用简单的时间标记
        start = time.time()
        
        # PDF解析
        t0 = time.time()
        stage_result = pipeline_func(*args, **kwargs)
        stages["pdf_parse"] = time.time() - t0
        
        # 记录
        self.metrics["total_time"].append(time.time() - start)
        for stage, duration in stages.items():
            self.metrics[f"{stage}_time"].append(duration)
        
        return stage_result, stages
    
    def profile_with_cprofile(self, func, *args, **kwargs):
        """使用cProfile进行详细分析"""
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # 前20个最耗时函数
        
        return result, s.getvalue()
    
    def get_summary(self):
        """获取性能摘要"""
        summary = {}
        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    "avg": round(sum(values) / len(values), 4),
                    "max": round(max(values), 4),
                    "min": round(min(values), 4),
                    "count": len(values)
                }
        return summary

class BottleneckAnalyzer:
    """瓶颈分析器"""
    
    def __init__(self, target_time=3.0):
        self.target_time = target_time
        self.bottlenecks = []
    
    def analyze(self, stage_times):
        """分析各阶段瓶颈"""
        total = sum(stage_times.values())
        
        analysis = []
        for stage, duration in stage_times.items():
            percentage = (duration / total * 100) if total > 0 else 0
            is_bottleneck = duration > self.target_time * 0.3  # 超过30%目标时间
            
            analysis.append({
                "stage": stage,
                "duration": round(duration, 3),
                "percentage": round(percentage, 1),
                "is_bottleneck": is_bottleneck,
                "severity": "high" if percentage > 40 else "medium" if percentage > 20 else "low"
            })
        
        analysis.sort(key=lambda x: x["duration"], reverse=True)
        
        self.bottlenecks = [a for a in analysis if a["is_bottleneck"]]
        return analysis
    
    def suggest_optimizations(self, bottlenecks):
        """给出优化建议"""
        suggestions = {
            "pdf_parse": [
                "使用MinerU代替PyMuPDF",
                "并行解析多页PDF",
                "缓存已解析的PDF"
            ],
            "embed": [
                "使用量化嵌入模型 (int8)",
                "批量编码减少调用次数",
                "使用GPU加速嵌入生成"
            ],
            "retrieval": [
                "使用IVF索引代替Flat索引",
                "减少检索的top_k",
                "使用PQ量化压缩向量"
            ],
            "generation": [
                "使用流式生成",
                "减小max_tokens",
                "使用更小的LLM模型"
            ],
            "chunk": [
                "预分块并缓存",
                "使用更小的chunk_size",
                "减少chunk overlap"
            ]
        }
        
        result = []
        for b in bottlenecks:
            stage = b["stage"].replace("_time", "")
            if stage in suggestions:
                result.append({
                    "stage": stage,
                    "current_time": b["duration"],
                    "suggestions": suggestions[stage]
                })
        
        return result

class LoadTester:
    """负载测试"""
    
    def __init__(self):
        self.results = []
    
    def test_concurrent(self, qa_func, questions, concurrency=5):
        """模拟并发测试"""
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def worker(q_list):
            for q in q_list:
                start = time.time()
                try:
                    answer = qa_func(q["question"])
                    elapsed = time.time() - start
                    result_queue.put({
                        "question": q["question"],
                        "success": True,
                        "time": elapsed
                    })
                except:
                    result_queue.put({
                        "question": q["question"],
                        "success": False,
                        "time": time.time() - start
                    })
        
        # 分配任务
        chunk_size = len(questions) // concurrency
        threads = []
        for i in range(concurrency):
            chunk = questions[i*chunk_size:(i+1)*chunk_size]
            t = threading.Thread(target=worker, args=(chunk,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        while not result_queue.empty():
            self.results.append(result_queue.get())
        
        return self._analyze_results()
    
    def _analyze_results(self):
        times = [r["time"] for r in self.results if r["success"]]
        return {
            "total": len(self.results),
            "success": sum(1 for r in self.results if r["success"]),
            "avg_time": round(sum(times)/len(times), 3) if times else 0,
            "max_time": round(max(times), 3) if times else 0,
            "p95_time": round(sorted(times)[int(len(times)*0.95)], 3) if len(times) > 1 else 0
        }

if __name__ == "__main__":
    print("性能瓶颈分析模块加载完成")
    print("\n分析工具:")
    print("  1. PerformanceProfiler - 各阶段耗时分析")
    print("  2. BottleneckAnalyzer - 瓶颈诊断与优化建议")
    print("  3. LoadTester - 并发负载测试")
    print(f"\n目标响应时间: < 3秒")
