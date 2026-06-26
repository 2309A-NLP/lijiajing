# -*- coding: utf-8 -*-
"""
work_order_17_智能备课 - Web 应用入口
教育智能体 - 基于 LLM 的智能备课辅助系统
工单编号：人工智能NLP-Agent数字人项目-17-智能备课
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from lesson_planner import planner
from config import WEB_HOST, WEB_PORT

app = FastAPI(title="工单17-智能备课", version="1.0")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 17 - 智能备课系统</title>
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
        .section-item { background: rgba(40,40,56,0.5); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
        .section-item h6 { color: var(--accent); margin-bottom: 0.5rem; }
        .bloom-badge { display: inline-block; padding: 0.2em 0.6em; border-radius: 4px; font-size: 0.75rem; margin: 0.1rem; }
        .bloom-covered { background: rgba(16,185,129,0.2); border: 1px solid var(--success); color: var(--success); }
        .bloom-missing { background: rgba(248,113,113,0.2); border: 1px solid #f87171; color: #f87171; }
        .progress-bar-custom { height: 8px; background: var(--surface-light); border-radius: 4px; overflow: hidden; margin-top: 0.5rem; }
        .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width 0.5s; }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-mortarboard" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>智能备课系统 Agent</h1>
            </div>
            <span class="badge">工单 17 · 教育智能体</span>
        </div>
    </div>
    <div class="main-container">
        <!-- 功能标签 -->
        <div class="mb-3">
            <span class="feature-tag"><i class="bi bi-list-check"></i> 课程大纲生成</span>
            <span class="feature-tag"><i class="bi bi-book"></i> 教学资源推荐</span>
            <span class="feature-tag"><i class="bi bi-easel"></i> 课件自动编排</span>
            <span class="feature-tag"><i class="bi bi-bullseye"></i> 教学目标对齐</span>
        </div>
        <div class="row g-4">
            <!-- 左侧：输入参数 -->
            <div class="col-lg-4">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-sliders"></i> 课程参数</div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">课程主题</label>
                        <input type="text" class="input-dark" id="topicInput" value="函数的单调性">
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">学科</label>
                        <select class="input-dark" id="subjectSelect">
                            <option value="数学">数学</option>
                            <option value="语文">语文</option>
                            <option value="英语">英语</option>
                            <option value="物理">物理</option>
                            <option value="化学">化学</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">年级</label>
                        <select class="input-dark" id="gradeSelect">
                            <option value="高一">高一</option>
                            <option value="高二">高二</option>
                            <option value="高三">高三</option>
                            <option value="初一">初一</option>
                            <option value="初二">初二</option>
                            <option value="初三">初三</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">课时数</label>
                        <input type="number" class="input-dark" id="hoursInput" value="2" min="1" max="5">
                    </div>
                    <div class="mb-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">目标 Bloom 层级</label>
                        <div class="d-flex flex-wrap gap-2">
                            <label class="d-flex align-items-center gap-1" style="font-size:0.85rem">
                                <input type="checkbox" value="理解" checked> 理解
                            </label>
                            <label class="d-flex align-items-center gap-1" style="font-size:0.85rem">
                                <input type="checkbox" value="应用" checked> 应用
                            </label>
                            <label class="d-flex align-items-center gap-1" style="font-size:0.85rem">
                                <input type="checkbox" value="分析" checked> 分析
                            </label>
                            <label class="d-flex align-items-center gap-1" style="font-size:0.85rem">
                                <input type="checkbox" value="评价"> 评价
                            </label>
                            <label class="d-flex align-items-center gap-1" style="font-size:0.85rem">
                                <input type="checkbox" value="创造"> 创造
                            </label>
                        </div>
                    </div>
                    <button class="btn-action" id="generateBtn" onclick="generate()">
                        <i class="bi bi-magic"></i> 一键生成备课方案
                    </button>
                </div>
            </div>
            <!-- 右侧：结果展示 -->
            <div class="col-lg-8">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-file-earmark-text"></i> 备课方案</div>
                    <div class="loading" id="loading"><div class="spinner"></div><p class="mt-2 text-muted">AI 正在生成备课方案...</p></div>
                    <div class="result-area" id="resultArea"><span class="text-muted">填写课程参数后点击「一键生成备课方案」</span></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        async function generate() {
            const loading = document.getElementById('loading'), resultArea = document.getElementById('resultArea'), btn = document.getElementById('generateBtn');
            loading.classList.add('active'); resultArea.innerHTML = ''; btn.disabled = true;
            
            const topic = document.getElementById('topicInput').value;
            const subject = document.getElementById('subjectSelect').value;
            const grade = document.getElementById('gradeSelect').value;
            const hours = parseInt(document.getElementById('hoursInput').value);
            const targetLevels = Array.from(document.querySelectorAll('input[type=checkbox]:checked')).map(cb => cb.value);
            
            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ topic, subject, grade, hours, target_levels: targetLevels })
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
            
            // 1. 课程大纲
            html += '<div class="section-item"><h6><i class="bi bi-list-check"></i> 课程大纲</h6>';
            html += '<div class="mb-2"><strong>主题：</strong>' + data.outline.topic + '</div>';
            html += '<div class="mb-2"><strong>学科/年级：</strong>' + data.outline.subject + ' · ' + data.outline.grade + '</div>';
            html += '<div class="mb-2"><strong>课时：</strong>' + data.outline.total_hours + ' 课时</div>';
            html += '<div class="mb-2"><strong>教学目标：</strong><ul class="mb-0">';
            data.outline.objectives.forEach(obj => { html += '<li>' + obj + '</li>'; });
            html += '</ul></div>';
            html += '<div class="mb-2"><strong>重点：</strong>' + data.outline.key_points.join('、') + '</div>';
            html += '<div><strong>难点：</strong>' + data.outline.difficulties.join('、') + '</div>';
            html += '</div>';
            
            // 2. 课程结构
            html += '<div class="section-item"><h6><i class="bi bi-clock-history"></i> 课程结构</h6>';
            data.outline.structure.forEach((s, i) => {
                html += '<div class="d-flex justify-content-between align-items-center mb-1">';
                html += '<span>' + (i+1) + '. ' + s.title + '</span>';
                html += '<span class="text-muted" style="font-size:0.85rem">' + s.minutes + '分钟</span>';
                html += '</div>';
            });
            html += '</div>';
            
            // 3. 推荐资源
            html += '<div class="section-item"><h6><i class="bi bi-book"></i> 推荐教学资源</h6>';
            data.resources.forEach(r => {
                html += '<div class="d-flex justify-content-between align-items-center mb-2 p-2" style="background:rgba(30,30,46,0.4);border-radius:8px">';
                html += '<div><strong>' + r.title + '</strong><br><span class="text-muted" style="font-size:0.8rem">' + r.type + ' · ' + r.reason + '</span></div>';
                html += '<span class="feature-tag">' + r.relevance + '</span>';
                html += '</div>';
            });
            html += '</div>';
            
            // 4. 课件编排
            html += '<div class="section-item"><h6><i class="bi bi-easel"></i> 课件编排</h6>';
            html += '<div class="mb-2"><strong>总页数：</strong>' + data.courseware.total_pages + ' 页</div>';
            html += '<div class="mb-2"><strong>预计时长：</strong>' + data.courseware.estimated_time + '</div>';
            html += '<div class="mb-0"><strong>幻灯片结构：</strong></div>';
            data.courseware.slides.forEach(s => {
                html += '<div class="ms-3 mb-1" style="font-size:0.9rem">📄 P' + s.page + ': ' + s.title + (s.duration ? ' (' + s.duration + ')' : '') + '</div>';
            });
            html += '</div>';
            
            // 5. 目标对齐
            const align = data.alignment;
            html += '<div class="section-item"><h6><i class="bi bi-bullseye"></i> 教学目标对齐 (Bloom)</h6>';
            html += '<div class="mb-2">';
            align.target_levels.forEach(level => {
                const covered = align.covered_levels.includes(level);
                html += '<span class="bloom-badge ' + (covered ? 'bloom-covered' : 'bloom-missing') + '">';
                html += (covered ? '✅ ' : '❌ ') + level + '</span> ';
            });
            html += '</div>';
            html += '<div class="mb-2"><strong>对齐度：</strong>' + align.alignment_score.toFixed(0) + '%</div>';
            html += '<div class="progress-bar-custom"><div class="progress-bar-fill" style="width:' + align.alignment_score + '%"></div></div>';
            if (align.suggestions.length > 0) {
                html += '<div class="mt-2" style="color:#fbbf24;font-size:0.85rem">💡 ' + align.suggestions[0] + '</div>';
            }
            html += '</div>';
            
            return html;
        }
    </script>
</body>
</html>
"""


@app.post("/generate")
async def generate(request: Request):
    """一键生成备课方案"""
    try:
        data = await request.json()
        topic = data.get("topic", "函数的单调性")
        subject = data.get("subject", "数学")
        grade = data.get("grade", "高一")
        hours = data.get("hours", 2)
        target_levels = data.get("target_levels", ["理解", "应用", "分析"])
        
        # 1. 生成课程大纲
        outline = planner.generate_outline(topic, subject, grade, hours)
        
        # 2. 推荐教学资源
        resources = planner.recommend_resources(subject, topic)
        
        # 3. 课件自动编排
        courseware = planner.arrange_courseware(outline)
        
        # 4. 教学目标对齐检查
        alignment = planner.check_alignment(outline, target_levels)
        
        return JSONResponse({
            "success": True,
            "data": {
                "outline": outline,
                "resources": resources,
                "courseware": courseware,
                "alignment": alignment,
            }
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok", "work_order": "work_order_17_智能备课"}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"📚 工单 17 - 智能备课系统")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{WEB_PORT}")
    print(f"📋 功能: 课程大纲生成 | 资源推荐 | 课件编排 | 目标对齐")
    print(f"{'='*60}\n")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
