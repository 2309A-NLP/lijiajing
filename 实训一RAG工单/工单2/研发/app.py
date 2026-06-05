"""
工单01 - Web界面 (Gradio)
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from qa_engine import RAGEngine

engine = None

def init_engine():
    global engine
    if engine is None:
        engine = RAGEngine()
    return engine

def answer_question(query, history=[]):
    engine = init_engine()
    result = engine.answer(query)
    
    response = result["answer"]
    
    # 添加引用和性能信息
    refs = ""
    if result["retrieved_chunks"]:
        refs = "\n\n---\n"
        refs += f"📄 引用来源: "
        for c in result["retrieved_chunks"][:3]:
            refs += f"[{c['chunk_id']}](p{c['page_num']}, 相似度:{c['score']:.2f}) "
        refs += f"\n⏱ 检索:{result['retrieval_time']:.2f}s | 生成:{result['generation_time']:.2f}s | 总计:{result['total_time']:.2f}s"
    
    return response + refs

# Gradio界面
def create_ui():
    import gradio as gr
    
    with gr.Blocks(title="工单01 - PDF问答系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 📚 RAG问答系统 - 工单01")
        gr.Markdown("基于《招股说明书1.pdf》的智能问答系统")
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="对话", height=500)
                msg = gr.Textbox(label="输入问题", placeholder="请输入问题...", scale=3)
                
                with gr.Row():
                    send_btn = gr.Button("发送", variant="primary")
                    clear_btn = gr.Button("清空")
            
            with gr.Column(scale=1):
                gr.Markdown("### 测试问题集")
                for q in [
                    "军用领域收入占比",
                    "技术标准",
                    "注册资本",
                    "法定代表人"
                ]:
                    gr.Button(q, size="sm")
        
        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            response = answer_question(message)
            chat_history.append((message, response))
            return "", chat_history
        
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        send_btn.click(respond, [msg, chatbot], [msg, chatbot])
        clear_btn.click(lambda: None, None, chatbot, queue=False)
    
    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
