# -*- coding: utf-8 -*-
"""
work_order_17_多模态知识检索 - Web 应用入口
文旅智能体 - 多模态知识检索系统
工单编号：人工智能NLP-Agent数字人项目-17-多模态知识检索
"""
import base64
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from multimodal_retriever import retriever
from config import WEB_HOST, WEB_PORT

app = FastAPI(title="工单17-多模态知识检索", version="1.0")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 17 - 多模态知识检索</title>
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
        .result-area { background: var(--surface-light); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; min-height: 200px; line-height: 1.8; font-size: 0.95rem; }
        .feature-tag { display: inline-block; padding: 0.3em 0.8em; border-radius: 6px; background: rgba(99,102,241,0.2); border: 1px solid var(--primary); color: var(--accent); font-size: 0.8rem; margin: 0.2rem; }
        .loading { display: none; text-align: center; padding: 2rem; } .loading.active { display: block; }
        .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .result-card { background: rgba(40,40,56,0.5); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; margin: 0.5rem 0; transition: all 0.3s; }
        .result-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 20px rgba(99,102,241,0.2); }
        .result-card h6 { color: var(--accent); margin-bottom: 0.5rem; }
        .score-bar { height: 6px; background: var(--surface-light); border-radius: 3px; overflow: hidden; margin-top: 0.5rem; }
        .score-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width 0.5s; }
        .upload-zone { border: 2px dashed var(--border); border-radius: 12px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.3s; background: rgba(40,40,56,0.5); }
        .upload-zone:hover { border-color: var(--primary); background: rgba(99,102,241,0.1); }
        .upload-zone i { font-size: 2.5rem; color: var(--primary); }
        .preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; margin-top: 1rem; border: 2px solid var(--border); }
        .mode-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
        .mode-tab { padding: 0.5rem 1rem; border-radius: 8px; background: var(--surface-light); border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.3s; font-size: 0.9rem; }
        .mode-tab.active { background: var(--primary); color: #fff; border-color: var(--primary); }
        .tag { display: inline-block; padding: 0.2em 0.6em; border-radius: 4px; background: rgba(34,211,238,0.15); color: var(--accent); font-size: 0.75rem; margin: 0.1rem; }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-images" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>多模态知识检索 Agent</h1>
            </div>
            <span class="badge">工单 17 · 文旅智能体</span>
        </div>
    </div>
    <div class="main-container">
        <div class="mb-3">
            <span class="feature-tag"><i class="bi bi-textarea-t"></i> 文本检索</span>
            <span class="feature-tag"><i class="bi bi-image"></i> 图片检索</span>
            <span class="feature-tag"><i class="bi bi-layers"></i> 多模态融合</span>
        </div>
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-search"></i> 检索模式</div>
                    <div class="mode-tabs">
                        <div class="mode-tab active" data-mode="text">📝 文本</div>
                        <div class="mode-tab" data-mode="image">🖼️ 图片</div>
                        <div class="mode-tab" data-mode="multimodal">🔀 融合</div>
                    </div>
                    
                    <div id="textInput">
                        <div class="mb-3">
                            <label class="text-muted mb-1" style="font-size:0.85rem">查询文本</label>
                            <textarea class="input-dark" id="queryText" rows="3" placeholder="例如：北京的古建筑、世界遗产...">北京的古建筑</textarea>
                        </div>
                    </div>
                    
                    <div id="imageInput" style="display:none">
                        <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                            <i class="bi bi-cloud-upload"></i>
                            <p class="mt-2 mb-0">点击上传图片</p>
                            <input type="file" id="fileInput" accept="image/*" onchange="handleFile(this.files[0])" hidden>
                        </div>
                        <img id="preview" class="preview-img" style="display:none">
                    </div>
                    
                    <div class="mb-3 mt-3">
                        <label class="text-muted mb-1" style="font-size:0.85rem">返回数量</label>
                        <select class="input-dark" id="topK">
                            <option value="3">Top 3</option>
                            <option value="5">Top 5</option>
                            <option value="10">Top 10</option>
                        </select>
                    </div>
                    
                    <button class="btn-action" id="searchBtn" onclick="search()">
                        <i class="bi bi-search"></i> 开始检索
                    </button>
                </div>
                
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-info-circle"></i> 知识库统计</div>
                    <div id="statsArea" class="text-muted" style="font-size:0.9rem">加载中...</div>
                </div>
            </div>
            
            <div class="col-lg-7">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-list-ul"></i> 检索结果</div>
                    <div class="loading" id="loading"><div class="spinner"></div><p class="mt-2 text-muted">正在检索...</p></div>
                    <div class="result-area" id="resultArea"><span class="text-muted">选择模式并输入查询后点击「开始检索」</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedMode = 'text';
        let selectedFile = null;
        
        // 模式切换
        document.querySelectorAll('.mode-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                selectedMode = tab.dataset.mode;
                
                document.getElementById('textInput').style.display = selectedMode === 'image' ? 'none' : 'block';
                document.getElementById('imageInput').style.display = selectedMode === 'text' ? 'none' : 'block';
            });
        });
        
        // 文件上传
        function handleFile(file) {
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('preview');
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
        
        // 加载统计
        async function loadStats() {
            try {
                const res = await fetch('/stats');
                const data = await res.json();
                const statsArea = document.getElementById('statsArea');
                statsArea.innerHTML = `
                    <div class="mb-2"><strong>总条目：</strong>${data.total_items}</div>
                    <div class="mb-2"><strong>类型分布：</strong></div>
                    ${Object.entries(data.type_distribution).map(([type, count]) => 
                        `<span class="tag">${type}: ${count}</span>`
                    ).join('')}
                    <div class="mt-2"><strong>支持模态：</strong> ${data.supported_modalities.join(', ')}</div>
                `;
            } catch (e) {
                console.error('加载统计失败:', e);
            }
        }
        
        // 检索
        async function search() {
            const loading = document.getElementById('loading'), resultArea = document.getElementById('resultArea'), btn = document.getElementById('searchBtn');
            loading.classList.add('active'); resultArea.innerHTML = ''; btn.disabled = true;
            
            const topK = parseInt(document.getElementById('topK').value);
            const queryText = document.getElementById('queryText').value;
            
            try {
                let res;
                if (selectedMode === 'text') {
                    res = await fetch('/search/text', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ query: queryText, top_k: topK })
                    });
                } else if (selectedMode === 'image') {
                    // 模拟图片向量（实际应该提取图片特征）
                    const mockEmbedding = [Math.random(), Math.random(), Math.random(), Math.random()];
                    res = await fetch('/search/image', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ embedding: mockEmbedding, top_k: topK })
                    });
                } else {
                    const mockEmbedding = [Math.random(), Math.random(), Math.random(), Math.random()];
                    res = await fetch('/search/multimodal', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ text_query: queryText, image_embedding: mockEmbedding, top_k: topK })
                    });
                }
                
                const data = await res.json();
                loading.classList.remove('active');
                
                if (data.success) {
                    resultArea.innerHTML = formatResults(data.results);
                } else {
                    resultArea.innerHTML = '<span style="color:#f87171">❌ ' + data.error + '</span>';
                }
            } catch (e) {
                loading.classList.remove('active');
                resultArea.innerHTML = '<span style="color:#f87171">❌ ' + e.message + '</span>';
            }
            btn.disabled = false;
        }
        
        function formatResults(results) {
            if (!results || results.length === 0) {
                return '<span class="text-muted">未找到匹配结果</span>';
            }
            
            let html = '';
            results.forEach((r, i) => {
                const scorePercent = (r.score * 100).toFixed(1);
                html += `
                    <div class="result-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6>#${i+1} ${r.title}</h6>
                                <div class="text-muted" style="font-size:0.85rem">${r.type} · ${r.description}</div>
                                <div class="mt-2">
                                    ${r.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                                </div>
                            </div>
                            <div class="text-end">
                                <div style="font-size:0.85rem;color:var(--accent)">${scorePercent}%</div>
                                <div style="font-size:0.75rem" class="text-muted">${r.match_type}</div>
                            </div>
                        </div>
                        <div class="score-bar">
                            <div class="score-fill" style="width:${scorePercent}%"></div>
                        </div>
                    </div>
                `;
            });
            
            return html;
        }
        
        // 初始化
        loadStats();
    </script>
</body>
</html>
"""


@app.post("/search/text")
async def search_text(request: Request):
    """文本检索"""
    try:
        data = await request.json()
        query = data.get("query", "")
        top_k = data.get("top_k", 3)
        
        results = retriever.search_by_text(query, top_k)
        return JSONResponse({"success": True, "results": results})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/search/image")
async def search_image(request: Request):
    """图片检索"""
    try:
        data = await request.json()
        embedding = data.get("embedding", [0.5, 0.5, 0.5, 0.5])
        top_k = data.get("top_k", 3)
        
        results = retriever.search_by_image(embedding, top_k)
        return JSONResponse({"success": True, "results": results})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/search/multimodal")
async def search_multimodal(request: Request):
    """多模态融合检索"""
    try:
        data = await request.json()
        text_query = data.get("text_query", "")
        image_embedding = data.get("image_embedding")
        top_k = data.get("top_k", 3)
        
        results = retriever.multimodal_search(text_query, image_embedding, top_k)
        return JSONResponse({"success": True, "results": results})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/stats")
async def get_stats():
    """获取知识库统计"""
    return retriever.get_stats()


@app.get("/health")
async def health():
    return {"status": "ok", "work_order": "work_order_17_多模态知识检索"}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"🖼️  工单 17 - 多模态知识检索")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{WEB_PORT}")
    print(f"📋 功能: 文本检索 | 图片检索 | 多模态融合")
    print(f"{'='*60}\n")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
