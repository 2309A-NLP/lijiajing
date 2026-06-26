# -*- coding: utf-8 -*-
"""
work_order 15 语音识别 - Web 应用 (实时识别 + 摘要)
工单编号：人工智能NLP-Agent数字人项目-15-实时语音识别、翻译与会议纪要
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from speech_engine import SpeechRecognizer, CallbackHandler
from config import HOST, PORT
import asyncio
import json
import time

app = FastAPI(title="工单15-语音识别", version="1.0")
recognizer = SpeechRecognizer()
callback_handler = CallbackHandler(recognizer)

# 连接管理
active_connections = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 15 - 实时语音识别</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root { --primary:#059669; --accent:#047857; --surface:#1e1e2e; --surface-light:#282838; --text:#e0e0e0; --text-muted:#a0a0b0; --border:#333348; --green:#34d399; --red:#f87171; }
        body { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); color: var(--text); font-family: 'Inter', 'PingFang SC', sans-serif; min-height: 100vh; margin: 0; }
        .header { background: rgba(30,30,46,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); padding: 1rem 2rem; position: sticky; top: 0; z-index: 100; }
        .header h1 { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
        .header .badge { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; padding: 0.3em 0.8em; border-radius: 20px; font-size: 0.75rem; }
        .main-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .card-glass { background: rgba(30,30,46,0.6); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; transition: all 0.3s ease-in-out; }
        .card-glass:hover { transform: scale(1.01); box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
        .card-title { font-size: 1.1rem; font-weight: 600; color: var(--accent); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .btn-record { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; border: none; border-radius: 50px; padding: 1rem 2rem; font-size: 1.1rem; font-weight: 600; width: 100%; cursor: pointer; transition: all 0.3s ease-in-out; }
        .btn-record:hover { box-shadow: 0 0 30px rgba(5,150,105,0.5); transform: scale(1.02); }
        .btn-record.recording { animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(5,150,105,0.4)} 50%{box-shadow:0 0 0 15px rgba(5,150,105,0)} }
        .transcript-area { background: var(--surface-light); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; }
        .chunk-card { padding: 0.75rem; margin: 0.25rem; border-radius: 8px; background: rgba(40,40,56,0.5); border-left: 3px solid var(--primary); transition: all 0.3s ease-in-out; }
        .chunk-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .chunk-card.final { border-left-color: var(--green); }
        .chunk-card.active { background: rgba(5,150,105,0.2); border-left-color: var(--accent); }
        .chunk-text { font-size: 0.95rem; line-height: 1.6; }
        .chunk-translation { font-size: 0.85rem; color: var(--accent); margin-top: 0.25rem; }
        .chunk-time { font-size: 0.75rem; color: var(--text-muted); }
        .summary-card { background: rgba(5,150,105,0.1); border: 1px solid var(--primary); border-radius: 12px; padding: 1.25rem; margin: 0.75rem 0; }
        .summary-title { color: var(--accent); font-weight: 600; margin-bottom: 0.5rem; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .status-dot.ready { background: var(--text-muted); }
        .status-dot.recording { background: var(--red); animation: blink 1s infinite; }
        .status-dot.done { background: var(--green); }
        @keyframes blink { 50%{opacity:0.3} }
        .tag { display: inline-block; padding: 0.2em 0.6em; border-radius: 4px; background: rgba(4,120,87,0.15); color: var(--accent); font-size: 0.8rem; margin: 0.15rem; }
        .wave-bar { width: 4px; height: 24px; background: var(--accent); border-radius: 2px; animation: wave 1.5s infinite; }
        .wave-bar:nth-child(2) { animation-delay: 0.2s; }
        .wave-bar:nth-child(3) { animation-delay: 0.4s; }
        @keyframes wave { 0%,100%{height:12px} 50%{height:24px} }
        .chunk-item.active { background: rgba(99,102,241,0.2); border-left-color: var(--accent); }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-mic" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>实时语音识别 Agent</h1>
            </div>
            <span class="badge">工单 15 · 通义听悟</span>
        </div>
    </div>
    <div class="main-container">
        <div class="row g-4">
            <!-- 左：精简控制 (col-lg-2) -->
            <div class="col-lg-2">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-sliders"></i> 控制</div>
                    <div class="d-flex gap-2 mb-2">
                        <label class="text-muted mb-0" style="font-size:0.8rem">语言</label>
                        <select class="form-select form-select-sm flex-grow-1" id="langSelect" style="background:var(--surface-light);color:var(--text);border-color:var(--border);font-size:0.85rem">
                            <option value="zh">中文</option>
                            <option value="en">英文</option>
                            <option value="ja">日语</option>
                        </select>
                    </div>
                    <div class="form-check form-switch mb-2">
                        <input type="checkbox" class="form-check-input" id="transCheck" checked style="background-color:var(--primary);border-color:var(--primary)">
                        <label class="form-check-label text-muted" style="font-size:0.85rem">翻译</label>
                    </div>
                    <div class="d-flex align-items-center gap-2 mb-3">
                        <span class="status-dot" id="statusDot"></span>
                        <span id="statusText" class="text-muted" style="font-size:0.85rem">就绪</span>
                    </div>
                    <button class="btn-record py-2 w-100" id="recordBtn" onclick="toggleRecord()">
                        <i class="bi bi-mic-fill"></i> 开始
                    </button>
                    <div id="sessionId" class="text-muted mt-2" style="font-size:0.75rem"></div>
                </div>
            </div>

            <!-- 中：主转写区 (col-lg-7) - 横向流式布局 -->
            <div class="col-lg-7">
                <div class="card-glass">
                    <div class="card-title d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-chat-text"></i> 实时转写</span>
                        <span class="badge bg-success-subtle text-success rounded-pill" style="font-size:0.75rem">实时</span>
                    </div>
                    <div class="transcript-area d-flex flex-wrap gap-2 p-3" id="transcriptArea">
                        <div class="text-center text-muted py-5 w-100">
                            <i class="bi bi-mic" style="font-size:3rem;color:var(--accent)"></i>
                            <p class="mt-2">点击"开始"开始实时转写</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 右：摘要 + 频谱图 (col-lg-3) -->
            <div class="col-lg-3">
                <div class="card-glass sticky-top" style="max-height:400px;overflow-y:auto;">
                    <div class="card-title"><i class="bi bi-journal-text"></i> 摘要</div>
                    <div id="summaryPanel" style="display:none">
                        <div id="summaryContent"></div>
                    </div>
                </div>
                <div class="card-glass mt-3">
                    <div class="card-title"><i class="bi bi-graph-up"></i> 实时频谱</div>
                    <canvas id="spectrum" width="200" height="80" class="w-100" style="border-radius:8px;background:rgba(40,40,56,0.3)"></canvas>
                </div>
            </div>
        </div>
    </div>
    <script>
        // 频谱图模拟逻辑
        const canvas = document.getElementById('spectrum');
        const ctx = canvas.getContext('2d');
        function drawSpectrum() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const bars = 32;
            const barWidth = canvas.width / bars;
            for (let i = 0; i < bars; i++) {
                const height = Math.random() * 40 + 20;
                const x = i * barWidth;
                const gradient = ctx.createLinearGradient(x, canvas.height - height, x, canvas.height);
                gradient.addColorStop(0, 'rgba(5,150,105,0.8)');
                gradient.addColorStop(1, 'rgba(4,120,87,0.4)');
                ctx.fillStyle = gradient;
                ctx.fillRect(x, canvas.height - height, barWidth - 1, height);
            }
        }
        setInterval(drawSpectrum, 100);

        let isRecording = false, sessionId = null, ws = null, chunkCount = 0;
        async function toggleRecord(){
            const btn = document.getElementById('recordBtn'), dot = document.getElementById('statusDot'), st = document.getElementById('statusText');
            if(!isRecording){
                btn.innerHTML='<i class="bi bi-stop-fill"></i> 停止'; btn.classList.add('recording');
                dot.className='status-dot recording'; st.textContent='识别中...';
                chunkCount=0; document.getElementById('transcriptArea').innerHTML='';
                const res = await fetch('/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:document.getElementById('langSelect').value,translate:document.getElementById('transCheck').checked})});
                const data = await res.json(); sessionId=data.session_id;
                document.getElementById('sessionId').textContent='会话: '+sessionId;
                startSimulation();
                isRecording=true;
            } else {
                btn.innerHTML='<i class="bi bi-mic-fill"></i> 开始'; btn.classList.remove('recording');
                dot.className='status-dot done'; st.textContent='已完成';
                const res = await fetch('/session/'+sessionId+'/stop',{method:'POST'});
                const data = await res.json();
                if(data?.summary) showSummary(data.summary);
                isRecording = false;
                ws?.close();
                ws = null;
                document.getElementById('summaryPanel').style.display = 'block';
            }
        }
        function startSimulation(){
            if(ws) ws.close();
            ws = new WebSocket('ws://'+location.host+'/ws/'+sessionId);
            ws.onmessage = (e) => {
                const d = JSON.parse(e.data); addChunk(d);
            };
        }
        function addChunk(d){
            chunkCount++;
            const area = document.getElementById('transcriptArea');
            if(chunkCount===1) area.innerHTML='';
            const div = document.createElement('div');
            div.className = 'chunk-card'+(d.is_final?' final':'')+(d.class==='active'?' active':'');
            div.innerHTML = '<div class="chunk-text">'+d.text+'</div>'+
                (d.translation?'<div class="chunk-translation">🌐 '+d.translation+'</div>':'')+
                '<div class="chunk-time">#'+d.chunk_id+' · '+new Date(d.timestamp*1000).toLocaleTimeString()+'</div>';
            area.appendChild(div);
        }
        function showSummary(s){
            if(!s) return;
            const panel = document.getElementById('summaryPanel');
            if(!panel) return;
            const content = document.getElementById('summaryContent');
            if(!content) return;
            content.innerHTML =
                '<div class="summary-card"><div class="summary-title">📋 全文摘要</div>'+s['全文摘要']+'</div>'+
                '<div class="summary-card"><div class="summary-title">📑 章节速览</div>'+
                s['章节速览'].map(c=>'<div style="margin:0.3rem 0"><strong>'+c.time+'</strong> '+c.title+' - '+c.summary+'</div>').join('')+
                '</div>'+
                '<div class="summary-card"><div class="summary-title">✅ 待办事项</div>'+
                s['待办事项'].map(t=>'<div style="margin:0.2rem 0">• '+t+'</div>').join('')+
                '</div>'+
                '<div class="summary-card"><div class="summary-title">🏷️ 关键词</div>'+
                s['关键词'].map(k=>'<span class="tag">'+k+'</span>').join('')+
                '</div>';
        }

        // 确保 DOM 加载完成后再绑定事件
        document.addEventListener('DOMContentLoaded', function() {
            // toggleRecord 已定义，无需重复
        });
    </script>
</body>
</html>
"""


@app.post("/session")
async def create_session(request: Request):
    data = await request.json()
    session = recognizer.create_session(
        lang=data.get("lang", "zh"),
        enable_translation=data.get("translate", True)
    )
    return session


@app.post("/session/{session_id}/stop")
async def stop_session(session_id: str):
    from fastapi.responses import JSONResponse
    result = recognizer.stop_session(session_id)
    return JSONResponse(content=result)


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    return recognizer.get_session(session_id)


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # 模拟实时音频流推送识别结果
        import asyncio
        for i in range(15):
            if session_id not in active_connections:
                break
            chunk = recognizer.process_audio_chunk(session_id)
            await websocket.send_text(json.dumps(chunk, ensure_ascii=False))
            await asyncio.sleep(1.2)
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(session_id, None)


@app.post("/callback")
async def callback(request: Request):
    """通义听悟回调接口"""
    data = await request.json()
    result = callback_handler.handle_callback(data.get("task_id", ""), data)
    return {"status": "received", "task_id": result.get("task_id")}


@app.get("/health")
async def health():
    return {"status": "ok", "active_sessions": len(active_connections)}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"🎙️  工单 15 - 实时语音识别、翻译与会议纪要")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
