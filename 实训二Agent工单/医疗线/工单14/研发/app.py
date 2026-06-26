# -*- coding: utf-8 -*-
"""
work_order_14 MCP - Web 应用入口
工单编号：人工智能NLP-Agent数字人项目-14-MCP
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from mcp_server import MedicalMCPServer
from config import WEB_HOST, WEB_PORT

app = FastAPI(title="工单14-MCP", version="1.0")
server = MedicalMCPServer()


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 14 - MCP 医疗出行服务</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root { --primary:#6366f1; --surface:#1e1e2e; --surface-light:#282838; --text:#e0e0e0; --text-muted:#a0a0b0; --border:#333348; --accent:#22d3ee; }
        body { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); color: var(--text); font-family: 'Inter', 'PingFang SC', sans-serif; min-height: 100vh; margin: 0; }
        .header { background: rgba(30,30,46,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); padding: 1rem 2rem; position: sticky; top: 0; z-index: 100; }
        .header h1 { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
        .header .badge { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; padding: 0.3em 0.8em; border-radius: 20px; font-size: 0.75rem; }
        .main-container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .card-glass { background: rgba(30,30,46,0.6); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; }
        .card-title { font-size: 1.1rem; font-weight: 600; color: var(--accent); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .input-dark { background: var(--surface-light); border: 1px solid var(--border); border-radius: 8px; color: var(--text); padding: 0.75rem 1rem; width: 100%; }
        .input-dark:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
        .btn-action { background: linear-gradient(135deg, var(--primary), #4f46e5); color: #fff; border: none; border-radius: 10px; padding: 0.75rem 1.5rem; font-weight: 600; width: 100%; margin-top: 0.5rem; cursor: pointer; transition: all 0.3s; }
        .btn-action:hover { box-shadow: 0 4px 20px rgba(99,102,241,0.4); transform: translateY(-2px); }
        .result-area { background: var(--surface-light); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; min-height: 150px; white-space: pre-wrap; line-height: 1.8; font-size: 0.95rem; }
        .tool-tag { display: inline-block; padding: 0.3em 0.8em; border-radius: 6px; background: rgba(99,102,241,0.2); border: 1px solid var(--primary); color: var(--accent); font-size: 0.8rem; margin: 0.2rem; }
        .item-card { background: rgba(40,40,56,0.5); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
        .loading { display: none; text-align: center; padding: 2rem; } .loading.active { display: block; }
        .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-map" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>MCP 医疗出行服务 Agent</h1>
            </div>
            <span class="badge">工单 14 · MCP Server</span>
        </div>
    </div>
    <div class="main-container">
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-tools"></i> 可用 MCP Tools</div>
                    <div id="toolList" class="mb-3"></div>
                </div>
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-sliders"></i> 查询参数</div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">城市</label>
                        <input type="text" class="input-dark" id="cityInput" value="北京">
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">医院关键词</label>
                        <input type="text" class="input-dark" id="hospitalInput" value="协和">
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">操作模式</label>
                        <select class="input-dark" id="modeSelect">
                            <option value="full">🚗 完整就医计划</option>
                            <option value="search">🏥 仅搜索医院</option>
                            <option value="route">🗺️ 路线规划</option>
                            <option value="nearby">🍽️ 周边配套</option>
                        </select>
                    </div>
                    <button class="btn-action" id="runBtn" onclick="run()">
                        <i class="bi bi-play-fill"></i> 执行查询
                    </button>
                </div>
            </div>
            <div class="col-lg-7">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-terminal"></i> 查询结果</div>
                    <div class="loading" id="loading"><div class="spinner"></div><p class="mt-2 text-muted">MCP Server 处理中...</p></div>
                    <div class="result-area" id="resultArea"><span class="text-muted">选择模式后点击"执行查询"</span></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        fetch('/tools').then(r=>r.json()).then(tools=>{
            document.getElementById('toolList').innerHTML = tools.map(t=>'<span class="tool-tag">'+t.name+'</span>').join('');
        });
        async function run(){
            const loading = document.getElementById('loading'), resultArea = document.getElementById('resultArea'), btn = document.getElementById('runBtn');
            loading.classList.add('active'); resultArea.innerHTML=''; btn.disabled=true;
            const data = {mode: document.getElementById('modeSelect').value, city: document.getElementById('cityInput').value, hospital: document.getElementById('hospitalInput').value};
            try{
                const res = await fetch('/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
                const r = await res.json(); loading.classList.remove('active');
                if(r.success) resultArea.innerHTML = formatResult(r.result);
                else resultArea.innerHTML = '<span style="color:#f87171">❌ '+r.error+'</span>';
            }catch(e){ loading.classList.remove('active'); resultArea.innerHTML='<span style="color:#f87171">❌ '+e.message+'</span>'; }
            btn.disabled=false;
        }
        function formatResult(d){ if(typeof d==='object') return '<pre style="margin:0;white-space:pre-wrap">'+JSON.stringify(d,null,2)+'</pre>'; return String(d).replace(/\\n/g,'<br>'); }
    </script>
</body>
</html>
"""


@app.get("/tools")
async def list_tools():
    return server.list_tools()


@app.post("/execute")
async def execute(request: Request):
    data = await request.json()
    mode = data.get("mode", "full")
    city = data.get("city", "北京")
    hospital = data.get("hospital", "")
    
    if mode == "full":
        result = server.call_tool("medical_travel_plan", {
            "city": city, "hospital_name": hospital, "need_route": True, "need_nearby": True
        })
    elif mode == "search":
        result = server.call_tool("search_hospital", {"city": city, "keyword": hospital or "医院"})
    elif mode == "route":
        result = server.call_tool("plan_route", {"origin": "116.3974,39.9093", "destination": "116.4183,39.9146", "mode": "driving"})
    elif mode == "nearby":
        result = server.call_tool("search_nearby", {"location": "116.4183,39.9146", "category": "餐饮"})
    else:
        return JSONResponse({"success": False, "error": f"未知模式: {mode}"}, status_code=400)
    
    return JSONResponse({"success": True, "result": result})


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "work_order_14_mcp"}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"🗺️  工单 14 - MCP 医疗出行服务")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{WEB_PORT}")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
