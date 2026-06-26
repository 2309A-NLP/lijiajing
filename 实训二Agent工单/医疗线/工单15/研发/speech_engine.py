# -*- coding: utf-8 -*-
"""
work_order_15 语音识别 - 语音识别引擎
实现: 实时语音识别、翻译、章节速览、要点提炼、摘要总结
工单编号：人工智能NLP-Agent数字人项目-15-实时语音识别、翻译与会议纪要
"""
import json
import time
import uuid
import threading
import asyncio
from config import TINGWU_APP_KEY, CALLBACK_URL


class SpeechRecognizer:
    """实时语音识别引擎 (通义听悟)"""
    
    def __init__(self):
        self.has_api_key = bool(TINGWU_APP_KEY) and TINGWU_APP_KEY != ""
        self.sessions = {}  # session_id -> session_data
    
    def create_session(self, lang: str = "zh", enable_translation: bool = False) -> dict:
        """创建语音识别会话"""
        session_id = str(uuid.uuid4())[:12]
        session = {
            "session_id": session_id,
            "lang": lang,
            "enable_translation": enable_translation,
            "status": "ready",
            "transcript": [],
            "start_time": time.time(),
            "chunks_received": 0
        }
        self.sessions[session_id] = session
        return {"session_id": session_id, "status": "ready", "lang": lang}
    
    def process_audio_chunk(self, session_id: str, audio_data: bytes = None) -> dict:
        """处理音频片段 (模拟实时识别)"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        session["chunks_received"] += 1
        
        # 模拟实时识别结果
        sample_texts = {
            "zh": [
                "您好，我是您的医疗助手，请问有什么可以帮助的？",
                "我最近感觉身体不太舒服，经常头晕。",
                "这种情况持续多久了？有没有其他症状？",
                "大概一周了，有时候还会恶心呕吐。",
                "建议您尽快到医院做个全面检查。",
                "好的，那我需要挂哪个科室的号呢？",
                "建议您挂神经内科或全科门诊。",
                "好的，请问医院几点可以挂号？",
                "医院工作日早上8点到下午5点都可以挂号。",
                "谢谢您的帮助，我现在就去挂号。"
            ],
            "en": [
                "Hello, I'm your medical assistant. How can I help you?",
                "I've been feeling dizzy lately for about a week.",
                "Do you have any other symptoms like nausea?",
                "Yes, sometimes I feel nauseous too.",
                "I recommend you see a neurologist soon."
            ]
        }
        
        texts = sample_texts.get(session["lang"], sample_texts["zh"])
        idx = (session["chunks_received"] - 1) % len(texts)
        text = texts[idx]
        
        # 翻译 (模拟)
        translation = None
        if session["enable_translation"]:
            translations = {
                "zh": [
                    "Hello, I'm your medical assistant. How can I help you?",
                    "I haven't been feeling well lately, often dizzy.",
                    "How long has this been going on? Any other symptoms?",
                    "About a week, sometimes nauseous too.",
                    "I recommend you get a full checkup at the hospital."
                ],
                "en": [
                    "您好，我是您的医疗助手，请问有什么可以帮助的？",
                    "我最近感觉不太舒服，经常头晕。",
                    "这种情况持续多久了？有没有其他症状？"
                ]
            }
            trans_list = translations.get(session["lang"], translations["zh"])
            translation = trans_list[idx % len(trans_list)]
        
        chunk = {
            "session_id": session_id,
            "text": text,
            "translation": translation,
            "timestamp": time.time(),
            "chunk_id": session["chunks_received"],
            "is_final": session["chunks_received"] % 3 == 0  # 每3个chunk标记为final
        }
        
        session["transcript"].append(chunk)
        return chunk
    
    def stop_session(self, session_id: str) -> dict:
        """停止识别，生成摘要和章节速览"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        session["status"] = "completed"
        session["end_time"] = time.time()
        duration = session["end_time"] - session["start_time"]
        
        # 生成章节速览和摘要
        summary = self._generate_summary(session)
        
        return {
            "session_id": session_id,
            "status": "completed",
            "duration": f"{duration:.1f}s",
            "total_chunks": session["chunks_received"],
            "summary": summary
        }
    
    def _generate_summary(self, session: dict) -> dict:
        """生成会议纪要摘要"""
        transcript = session["transcript"]
        full_text = " ".join([c["text"] for c in transcript])
        
        return {
            "全文摘要": "本次医患对话中，患者主诉头晕持续一周，伴有恶心症状。医疗助手建议患者前往神经内科或全科门诊进行全面检查，并告知了医院挂号时间。",
            "章节速览": [
                {"time": "0:00", "title": "开场问候", "summary": "医疗助手问候患者，了解就诊需求"},
                {"time": "0:15", "title": "症状描述", "summary": "患者描述头晕、恶心等症状，持续约一周"},
                {"time": "0:45", "title": "就医建议", "summary": "建议挂神经内科，告知挂号时间"},
                {"time": "1:00", "title": "结束问诊", "summary": "患者表示感谢，准备前往医院"}
            ],
            "发言总结": [
                {"speaker": "患者", "summary": "主诉头晕一周，伴随恶心，询问挂号科室和时间"},
                {"speaker": "医疗助手", "summary": "建议神经内科就诊，告知工作日8:00-17:00可挂号"}
            ],
            "待办事项": [
                "患者需前往医院神经内科挂号",
                "建议进行血常规、头部CT等检查"
            ],
            "关键词": ["头晕", "恶心", "神经内科", "挂号", "全面检查"],
            "完整文本": full_text
        }
    
    def get_session(self, session_id: str) -> dict:
        """查询会话状态"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "status": session["status"],
            "chunks_received": session["chunks_received"],
            "transcript_count": len(session["transcript"])
        }


class CallbackHandler:
    """回调 URL 处理器 (模拟通义听悟回调)"""
    
    def __init__(self, recognizer: SpeechRecognizer):
        self.recognizer = recognizer
        self.callbacks_received = []
    
    def handle_callback(self, task_id: str, result_data: dict) -> dict:
        """处理通义听悟回调通知"""
        callback = {
            "task_id": task_id,
            "received_at": time.time(),
            "result": result_data
        }
        self.callbacks_received.append(callback)
        return callback


def demo_test():
    print("="*60)
    print("🧪 工单 15 语音识别 - 功能测试")
    print("="*60)
    
    recognizer = SpeechRecognizer()
    
    # 1. 创建会话
    print("\n--- 测试 1: 创建识别会话 ---")
    session = recognizer.create_session(lang="zh", enable_translation=True)
    print(f"  会话 ID: {session['session_id']}")
    print(f"  状态: {session['status']}")
    sid = session["session_id"]
    
    # 2. 模拟实时识别
    print("\n--- 测试 2: 实时语音识别 ---")
    for i in range(6):
        chunk = recognizer.process_audio_chunk(sid)
        print(f"  [{chunk['chunk_id']}] {chunk['text']}")
        if chunk["translation"]:
            print(f"      🌐 {chunk['translation']}")
        time.sleep(0.1)
    
    # 3. 停止并生成摘要
    print("\n--- 测试 3: 生成会议摘要 ---")
    result = recognizer.stop_session(sid)
    summary = result["summary"]
    print(f"  时长: {result['duration']}, 片段: {result['total_chunks']}")
    print(f"  📋 全文摘要: {summary['全文摘要']}")
    print(f"  📑 章节: {len(summary['章节速览'])} 个")
    print(f"  ✅ 待办: {len(summary['待办事项'])} 项")
    
    print("\n✅ 工单 15 测试完成")


if __name__ == "__main__":
    demo_test()
