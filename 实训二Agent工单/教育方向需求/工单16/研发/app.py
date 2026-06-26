# -*- coding: utf-8 -*-
"""
work_order_16_教育需求分析 - Web 应用入口
教育智能体 - 需求分析与功能设计
工单编号：人工智能NLP-Agent数字人项目-16-教育需求分析
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from education_analyzer import analyzer
from config import WEB_HOST, WEB_PORT

app = FastAPI(title="工单16-教育需求分析", version="1.0")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 16 - 教育需求分析</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root { --primary:#6366f1; --surface:#1e1e2e; --surface-light:#282838; --text:#e0e0e0; --text-muted:#a0a0b0; --border:#333348; --accent:#22d3ee; --success:#10b981; }
        body { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); color: var(--text); font-family: 'Inter', 'PingFang SC', sans-serif; min-height: 100vh; margin: 0; }
        .header { background: rgba(30,30,46,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); padding: 1rem 2rem; position: sticky; top: 0; z-index: 100; }
        .header h1 { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
        .header .badge { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; padding: 0.3em 0.8em; border-radius: 20px; font-size: 0.75rem; }
        .main-container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .card-glass { background: rgba(30,30,46,0.6); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; }
        .card-title { font-size: 1.1rem; font-weight: 600; color: var(--accent); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .input-dark { background: var(--surface-light); border: 1px solid var(--border); border-radius: 8px; color: var(--text); padding: 0.75rem 1rem; width: 100%; }
        .input-dark:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
        .btn-action { background: linear-gradient(135deg, var(--primary), #4f46e5); color: #fff; border: none; border-radius: 10px; padding: 0.75rem 1.5rem; font-weight: 600; width: 100%; margin-top: 0.5rem; cursor: pointer; transition: all 0.3s; }
        .btn-action:hover { box-shadow: 0 4px 20px rgba(99,102,241,0.4); transform: translateY(-2px); }
        .btn-action:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .result-area { background: var(--surface-light); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; min-height: 200px; white-space: pre-wrap; line-height: 1.8; font-size: 0.95rem; }
        .feature-tag { display: inline-block; padding: 0.3em 0.8em; border-radius: 6px; background: rgba(99,102,241,0.2); border: 1px solid var(--primary); color: var(--accent); font-size: 0.8rem; margin: 0.2rem; }
        .loading { display: none; text-align: center; padding: 2rem; } .loading.active { display: block; }
        .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .pain-card { background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
        .pain-card h6 { color: #f87171; margin-bottom: 0.5rem; }
        .scenario-card { background: rgba(34,211,238,0.1); border: 1px solid rgba(34,211,238,0.3); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
        .scenario-card h6 { color: var(--accent); margin-bottom: 0.5rem; }
        .arch-layer { background: rgba(99,102,241,0.1); border: 1px solid var(--primary); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
        .arch-layer h6 { color: var(--primary); margin-bottom: 0.5rem; }
        .value-metric { display: inline-block; padding: 0.3em 0.8em; border-radius: 6px; background: rgba(16,185,129,0.2); border: 1px solid var(--success); color: var(--success); font-size: 0.85rem; margin: 0.2rem; }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-mortarboard" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>教育需求分析 Agent</h1>
            </div>
            <span class="badge">工单 16 · 教育智能体</span>
        </div>
    </div>
    <div class="main-container">
        <div class="mb-3">
            <span class="feature-tag"><i class="bi bi-exclamation-triangle"></i> 痛点分析</span>
            <span class="feature-tag"><i class="bi bi-robot"></i> AI 场景</span>
            <span class="feature-tag"><i class="bi bi-diagram-3"></i> 功能架构</span>
            <span class="feature-tag"><i class="bi bi-graph-up-arrow"></i> 价值评估</span>
        </div>
        <div class="row g-4">
            <div class="col-lg-4">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-sliders"></i> 分析参数</div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">教育类型</label>
                        <select class="input-dark" id="educationType">
                            <option value="职业教育">职业教育</option>
                            <option value="基础教育">基础教育</option>
                            <option value="高等教育">高等教育</option>
                            <option value="在线教育">在线教育</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">重点需求（可选）</label>
                        <textarea class="input-dark" id="requirements" rows="3" placeholder="例如：提升备课效率，个性化教学..."></textarea>
                    </div>
                    <button class="btn-action" id="analyzeBtn" onclick="analyze()">
                        <i class="bi bi-search"></i> 开始需求分析
                    </button>
                </div>
            </div>
            <div class="col-lg-8">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-file-earmark-text"></i> 分析报告</div>
                    <div class="loading" id="loading"><div class="spinner"></div><p class="mt-2 text-muted">AI 正在分析需求...</p></div>
                    <div class="result-area" id="resultArea"><span class="text-muted">选择教育类型后点击「开始需求分析」</span></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        async function analyze() {
            const loading = document.getElementById('loading'), resultArea = document.getElementById('resultArea'), btn = document.getElementById('analyzeBtn');
            loading.classList.add('active'); resultArea.innerHTML = ''; btn.disabled = true;
            
            const educationType = document.getElementById('educationType').value;
            const requirements = document.getElementById('requirements').value;
            
            try {
                const res = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ education_type: educationType, requirements })
                });
                const r = await res.json();
                loading.classList.remove('active');
                if (r.success) {
                    resultArea.innerHTML = formatResult(r.data);
                } else {
                    resultArea.innerHTML = '<span style="color:#f87171">❌ ' + r.error + '</span>';
                }
            } catch (e) {
                loading.classList.remove('active');
                resultArea.innerHTML = '<span style="color:#f87171">❌ ' + e.message + '</span>';
            }
            btn.disabled = false;
        }
        
        function formatResult(data) {
            let html = '';
            
            // 1. 痛点分析
            html += '<div class="pain-card"><h6><i class="bi bi-exclamation-triangle"></i> 核心痛点</h6>';
            html += '<div class="mb-2"><strong>核心问题：</strong>' + data.pain_points.core_issue + '</div>';
            html += '<div class="mb-2"><strong>机会点：</strong>' + data.pain_points.opportunity + '</div>';
            html += '<div class="mt-3">';
            for (const [category, pains] of Object.entries(data.pain_points.pain_points)) {
                html += '<div class="mb-2"><strong>' + category + '：</strong>';
                html += pains.map(p => '<div class="ms-3">• ' + p + '</div>').join('');
                html += '</div>';
            }
            html += '</div></div>';
            
            // 2. AI 应用场景
            html += '<div class="scenario-card"><h6><i class="bi bi-robot"></i> AI 教育应用场景</h6>';
            data.scenarios.forEach(s => {
                html += '<div class="mb-3 p-2" style="background:rgba(30,30,46,0.4);border-radius:8px">';
                html += '<div class="mb-1"><strong>' + s.name + '</strong></div>';
                html += '<div class="text-muted" style="font-size:0.9rem">' + s.description + '</div>';
                html += '<div class="mt-2">';
                s.tech.forEach(t => { html += '<span class="feature-tag">' + t + '</span>'; });
                html += '</div>';
                html += '<div class="mt-2" style="color:var(--success);font-size:0.85rem">💡 ' + s.value + '</div>';
                html += '</div>';
            });
            html += '</div>';
            
            // 3. 系统架构
            html += '<div class="arch-layer"><h6><i class="bi bi-diagram-3"></i> 系统功能架构</h6>';
            html += '<div class="mb-2"><strong>数据流：</strong>' + data.architecture.data_flow + '</div>';
            for (const [layer, components] of Object.entries(data.architecture.layers)) {
                html += '<div class="mb-2"><strong>' + layer + '：</strong>';
                components.forEach(c => { html += '<span class="feature-tag">' + c + '</span>'; });
                html += '</div>';
            }
            html += '<div class="mt-3"><strong>核心组件：</strong>';
            data.architecture.key_components.forEach(c => { html += '<div class="ms-3">• ' + c + '</div>'; });
            html += '</div></div>';
            
            // 4. 价值评估
            html += '<div class="scenario-card"><h6><i class="bi bi-graph-up-arrow"></i> 项目价值评估</h6>';
            for (const [dimension, info] of Object.entries(data.value)) {
                html += '<div class="mb-2">';
                html += '<strong>' + dimension + '：</strong> ' + info.improvement + '<br>';
                html += '<span class="text-muted" style="font-size:0.85rem">指标：';
                info.metrics.forEach(m => { html += '<span class="value-metric">' + m + '</span>'; });
                html += '</span></div>';
            }
            html += '</div>';
            
            return html;
        }
    </script>
</body>
</html>
"""


@app.post("/analyze")
async def analyze_endpoint(request: Request):
    """需求分析接口"""
    try:
        data = await request.json()
        education_type = data.get("education_type", "职业教育")
        requirements = data.get("requirements", "")
        
        # 1. 痛点分析
        pain_points = analyzer.analyze_pain_points(education_type)
        
        # 2. AI 应用场景
        scenarios = analyzer.generate_ai_scenarios(requirements)
        
        # 3. 系统架构
        architecture = analyzer.design_architecture()
        
        # 4. 价值评估
        value = analyzer.estimate_value()
        
        return JSONResponse({
            "success": True,
            "data": {
                "pain_points": pain_points,
                "scenarios": scenarios,
                "architecture": architecture,
                "value": value,
            }
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok", "work_order": "work_order_16_教育需求分析"}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"📚 工单 16 - 教育需求分析")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{WEB_PORT}")
    print(f"📋 功能: 痛点分析 | AI场景 | 功能架构 | 价值评估")
    print(f"{'='*60}\n")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
