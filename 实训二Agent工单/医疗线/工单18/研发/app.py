# 工单编号：人工智能NLP-Agent数字人项目-18-智能导览
"""
文旅智能体 - 智能导览
Gradio UI 界面
"""
import gradio as gr
from agent import (
    agent, search_spot, generate_commentary, 
    recommend_route, nearby_recommendation, generate_audio_script
)

WELCOME = (
    "🏛️ 欢迎使用智能导览！\n"
    "我可以帮你：\n"
    "• 景点解说（如：介绍一下故宫）\n"
    "• 推荐游览路线（如：北京一日游路线）\n"
    "• 附近景点推荐（如：附近有什么景点？）\n"
    "• 生成语音导览词（如：生成故宫的语音导览）"
)


def on_submit(message: str, history: list):
    """处理用户输入"""
    if not message.strip():
        return "", history
    
    reply = agent.chat(message.strip())
    history.append((message, reply))
    return "", history


def reset_all():
    """重置对话"""
    agent.reset()
    return [(None, WELCOME)], ""


def show_spot_info(spot_name: str):
    """展示景点信息"""
    info = search_spot(spot_name)
    if "error" in info:
        return f"❌ {info['error']}"
    
    output = f"【{info['name']}】\n\n"
    output += f"📍 位置：{info['location']['lat']}, {info['location']['lng']}\n"
    output += f"📝 简介：{info['description']}\n"
    output += f"📜 历史：{info['history']}\n\n"
    output += f"🎯 看点：\n" + "\n".join([f"  • {h}" for h in info['highlights']]) + "\n\n"
    output += f"⏰ 游览时间：{info['visit_time']}\n"
    output += f"🎫 门票：{info['ticket']}\n"
    return output


def show_tour_route(duration: str, interest: str):
    """展示游览路线"""
    route = recommend_route(duration, interest)
    output = f"🗺️ 推荐路线：{route['route_name']}\n\n"
    for i, spot in enumerate(route['spots'], 1):
        output += f"{i}. {spot['spot']}\n"
        output += f"   时间：{spot['time']} ({spot['duration']})\n\n"
    return output


def show_nearby_spots(lat: float, lng: float, radius: float):
    """展示附近景点"""
    nearby = nearby_recommendation(lat, lng, radius)
    output = f"📍 位置：{lat}, {lng}\n"
    output += f"🔍 搜索半径：{radius}km\n\n"
    
    if not nearby:
        return output + "未找到附近景点"
    
    output += "附近景点：\n\n"
    for spot in nearby:
        if "name" in spot:
            output += f"• {spot['name']} ({spot['distance']})\n"
            output += f"  {spot['description']}\n\n"
        else:
            output += spot.get("message", "未找到景点")
    return output


def generate_audio(spot_name: str, language: str):
    """生成语音导览脚本"""
    script = generate_audio_script(spot_name, language)
    return script


def show_call_log():
    """展示调用日志"""
    if not agent.call_log:
        return "暂无调用记录"
    
    lines = []
    for i, log in enumerate(agent.call_log, 1):
        lines.append(f"═══ 第 {i} 次调用 [{log['time']}] ═══")
        lines.append(f"  操作：{log['action']}")
        lines.append(f"  结果：{log['result']}")
        lines.append("")
    return "\n".join(lines)


# ───────── Gradio UI ─────────

with gr.Blocks(title="智能导览", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏛️ 智能导览")
    gr.Markdown("AI 驱动的智慧景区导览系统")
    
    with gr.Tab("💬 智能导览对话"):
        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME}],
            height=460,
            label="对话窗口"
        )
        with gr.Row():
            msg_box = gr.Textbox(
                placeholder="输入问题，如：介绍一下故宫",
                scale=9,
                label="",
                show_label=False
            )
            send_btn = gr.Button("发送 ▶", scale=1, variant="primary")
        
        gr.Examples(
            label="测试问题（点击填入）",
            examples=[
                ["介绍一下故宫"],
                ["北京一日游路线"],
                ["附近有什么景点？"],
                ["生成故宫的语音导览"],
            ],
            inputs=msg_box
        )
        
        reset_btn = gr.Button("🔄 清空对话", variant="secondary", size="sm")
    
    with gr.Tab("🏛️ 景点信息查询"):
        gr.Markdown("查询景点详细信息")
        spot_input = gr.Textbox(
            placeholder="景点名称，如：故宫",
            label="景点名称"
        )
        query_btn = gr.Button("🔍 查询", variant="primary")
        spot_output = gr.Textbox(label="景点信息", lines=12, interactive=False)
        
        query_btn.click(
            show_spot_info,
            inputs=spot_input,
            outputs=spot_output
        )
    
    with gr.Tab("🗺️ 游览路线推荐"):
        gr.Markdown("推荐个性化游览路线")
        with gr.Row():
            duration_dropdown = gr.Dropdown(
                choices=["一日", "两日", "三日"],
                value="一日",
                label="游览时长"
            )
            interest_dropdown = gr.Dropdown(
                choices=["文化", "自然", "美食", "购物"],
                value="文化",
                label="兴趣偏好"
            )
        route_btn = gr.Button("📋 生成路线", variant="primary")
        route_output = gr.Textbox(label="推荐路线", lines=10, interactive=False)
        
        route_btn.click(
            show_tour_route,
            inputs=[duration_dropdown, interest_dropdown],
            outputs=route_output
        )
    
    with gr.Tab("📍 LBS附近推荐"):
        gr.Markdown("基于位置推荐附近景点")
        with gr.Row():
            lat_input = gr.Number(value=39.9, label="纬度")
            lng_input = gr.Number(value=116.4, label="经度")
            radius_input = gr.Number(value=5.0, label="搜索半径(km)")
        nearby_btn = gr.Button("🔍 搜索附近", variant="primary")
        nearby_output = gr.Textbox(label="附近景点", lines=10, interactive=False)
        
        nearby_btn.click(
            show_nearby_spots,
            inputs=[lat_input, lng_input, radius_input],
            outputs=nearby_output
        )
    
    with gr.Tab("🎙️ 语音导览生成"):
        gr.Markdown("生成语音导览脚本")
        with gr.Row():
            audio_spot_input = gr.Textbox(
                placeholder="景点名称，如：故宫",
                label="景点名称"
            )
            language_dropdown = gr.Dropdown(
                choices=["中文", "英文", "日语"],
                value="中文",
                label="语言"
            )
        audio_btn = gr.Button("🎤 生成导览词", variant="primary")
        audio_output = gr.Textbox(label="导览脚本", lines=15, interactive=False)
        
        audio_btn.click(
            generate_audio,
            inputs=[audio_spot_input, language_dropdown],
            outputs=audio_output
        )
    
    with gr.Tab("🔍 调用日志"):
        gr.Markdown("查看 Agent 调用记录")
        log_btn = gr.Button("🔄 刷新日志", variant="secondary", size="sm")
        log_output = gr.Textbox(label="调用日志", lines=20, interactive=False)
        
        log_btn.click(show_call_log, outputs=log_output)
    
    # 事件绑定
    send_btn.click(on_submit, inputs=[msg_box, chatbot], outputs=[msg_box, chatbot])
    msg_box.submit(on_submit, inputs=[msg_box, chatbot], outputs=[msg_box, chatbot])
    reset_btn.click(reset_all, outputs=[chatbot, msg_box])


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7878,
        share=False,
        inbrowser=True
    )
