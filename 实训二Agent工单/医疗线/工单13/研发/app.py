# -*- coding: utf-8 -*-
"""
work_order_13 影像分析 - Web 应用入口
工单编号：人工智能NLP-Agent数字人项目-13-影像分析
"""
import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from image_analyzer import MedicalImageAnalyzer
from config import HOST, PORT, UPLOAD_DIR, STATIC_DIR

app = FastAPI(title="工单13-影像分析", version="1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
analyzer = MedicalImageAnalyzer()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>工单 13 - 医疗影像分析</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --surface: #1e1e2e;
            --surface-light: #282838;
            --text: #e0e0e0;
            --text-muted: #a0a0b0;
            --border: #333348;
            --accent: #22d3ee;
            --success: #34d399;
        }
        * { box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            color: var(--text);
            font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            min-height: 100vh;
            margin: 0;
        }
        .header {
            background: rgba(30, 30, 46, 0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .header .badge {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            color: #fff;
            padding: 0.3em 0.8em;
            border-radius: 20px;
            font-size: 0.75rem;
        }
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .card-glass {
            background: rgba(30, 30, 46, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }
        .card-glass:hover {
            border-color: var(--primary);
            box-shadow: 0 0 30px rgba(99, 102, 241, 0.15);
        }
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .upload-zone {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: rgba(40, 40, 56, 0.5);
        }
        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
        }
        .upload-zone i { font-size: 3rem; color: var(--primary); }
        .upload-zone p { color: var(--text-muted); margin: 0.5rem 0 0; }
        .preview-img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 12px;
            margin-top: 1rem;
            border: 2px solid var(--border);
        }
        .btn-action {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s;
            width: 100%;
            margin-top: 0.5rem;
        }
        .btn-action:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        }
        .btn-action:disabled {
            opacity: 0.5;
            transform: none;
            box-shadow: none;
        }
        .result-area {
            background: var(--surface-light);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            min-height: 200px;
            white-space: pre-wrap;
            line-height: 1.8;
            font-size: 0.95rem;
        }
        .result-area .label {
            color: var(--accent);
            font-weight: 600;
        }
        .thinking-box {
            background: rgba(34, 211, 238, 0.1);
            border-left: 3px solid var(--accent);
            border-radius: 0 8px 8px 0;
            padding: 0.75rem 1rem;
            margin-top: 1rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        .loading.active { display: block; }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .tab-pills {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .tab-pill {
            padding: 0.5rem 1.2rem;
            border-radius: 8px;
            background: var(--surface-light);
            border: 1px solid var(--border);
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
        }
        .tab-pill.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }
        .input-dark {
            background: var(--surface-light);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            padding: 0.75rem 1rem;
            width: 100%;
        }
        .input-dark:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-lungs" style="font-size:1.8rem;color:var(--accent)"></i>
                <h1>医疗影像分析 Agent</h1>
            </div>
            <span class="badge">工单 13 · VQA + MRG + RAG</span>
        </div>
    </div>

    <div class="main-container">
        <div class="row g-4">
            <!-- 左侧：上传与操作 -->
            <div class="col-lg-5">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-cloud-upload"></i> 上传影像</div>
                    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                        <i class="bi bi-cloud-upload"></i>
                        <p>点击此处选择医学影像图片</p>
                        <p style="font-size:0.8rem;color:#666">支持 JPG, PNG</p>
                        <input type="file" id="fileInput" accept="image/*" onchange="handleFile(this.files[0])" hidden>
                    </div>
                    <img id="preview" class="preview-img" style="display:none">
                    
                    <div class="mt-3">
                        <label class="text-muted mb-2" style="font-size:0.85rem">提问 (VQA 模式)</label>
                        <input type="text" class="input-dark" id="questionInput" placeholder="例如：这张X光片显示了什么异常？" value="请分析这张医学影像">
                    </div>

                    <div class="tab-pills mt-3">
                        <div class="tab-pill active" data-mode="vqa">🔍 VQA 问答</div>
                        <div class="tab-pill" data-mode="mrg">📋 报告生成</div>
                        <div class="tab-pill" data-mode="rag">🔗 RAG 增强</div>
                    </div>

                    <button class="btn-action" id="analyzeBtn" disabled onclick="analyze()">
                        <i class="bi bi-cpu"></i> 开始分析
                    </button>
                </div>

                <!-- 功能说明 -->
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-info-circle"></i> 功能说明</div>
                    <div style="font-size:0.85rem;color:var(--text-muted);line-height:1.8">
                        <div><strong style="color:var(--text)">🔍 VQA</strong> - 视觉问答，上传图片并提问</div>
                        <div><strong style="color:var(--text)">📋 MRG</strong> - 自动生成标准化医疗诊断报告</div>
                        <div><strong style="color:var(--text)">🔗 RAG</strong> - 结合知识图谱增强分析</div>
                    </div>
                </div>
            </div>

            <!-- 右侧：分析结果 -->
            <div class="col-lg-7">
                <div class="card-glass">
                    <div class="card-title"><i class="bi bi-clipboard-data"></i> 分析结果</div>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p class="mt-2 text-muted">AI 正在分析影像，请稍候...</p>
                    </div>
                    <div class="result-area" id="resultArea">
                        <span class="text-muted">上传图片并点击"开始分析"后，结果将显示在这里</span>
                    </div>
                    <div class="thinking-box" id="thinkingBox" style="display:none"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedMode = 'vqa';
        let selectedFile = null;
        let uploadedUrl = null;

        // 模式切换
        document.querySelectorAll('.tab-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.tab-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                selectedMode = pill.dataset.mode;
            });
        });

        // 文件上传
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');

        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
        uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', (e) => { if (e.target.files.length) handleFile(e.target.files[0]); });

        function handleFile(file) {
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
                document.getElementById('analyzeBtn').disabled = false;
            };
            reader.readAsDataURL(file);
        }

        async function analyze() {
            if (!selectedFile) return;
            const loading = document.getElementById('loading');
            const resultArea = document.getElementById('resultArea');
            const thinkingBox = document.getElementById('thinkingBox');
            const btn = document.getElementById('analyzeBtn');

            loading.classList.add('active');
            resultArea.innerHTML = '';
            thinkingBox.style.display = 'none';
            btn.disabled = true;

            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('mode', selectedMode);
            formData.append('question', document.getElementById('questionInput').value);

            try {
                const res = await fetch('/analyze', { method: 'POST', body: formData });
                const data = await res.json();
                loading.classList.remove('active');

                if (data.success) {
                    const content = data.report || data.answer || data.final_answer || '分析完成';
                    resultArea.innerHTML = formatResult(content);
                    if (data.thinking) {
                        thinkingBox.innerHTML = '🧠 <strong>Agent 思考链:</strong> ' + data.thinking;
                        thinkingBox.style.display = 'block';
                    }
                } else {
                    resultArea.innerHTML = '<span style="color:#f87171">❌ 分析失败: ' + (data.error || '未知错误') + '</span>';
                }
            } catch (e) {
                loading.classList.remove('active');
                resultArea.innerHTML = '<span style="color:#f87171">❌ 网络错误: ' + e.message + '</span>';
            }
            btn.disabled = false;
        }

        function formatResult(text) {
            return text
                .replace(/\\[(.+?)\\]/g, '<span class="label">[$1]</span>')
                .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\n/g, '<br>');
        }
    </script>
</body>
</html>
"""


@app.post("/analyze")
async def analyze_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("vqa"),
    question: str = Form("请分析这张医学影像")
):
    """分析接口"""
    try:
        # 保存上传文件
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        if mode == "vqa":
            result = analyzer.vqa(filepath, question)
        elif mode == "mrg":
            result = analyzer.generate_report(filepath)
        elif mode == "rag":
            result = analyzer.rag_enhanced_analysis(filepath, question)
        else:
            return JSONResponse({"success": False, "error": f"未知模式: {mode}"}, status_code=400)

        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "work_order_13", "endpoints": ["/", "/analyze", "/health"]}


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*60}")
    print(f"🏥 工单 13 - 医疗影像分析 Agent")
    print(f"{'='*60}")
    print(f"🌐 访问: http://localhost:{PORT}")
    print(f"📁 上传目录: {UPLOAD_DIR}")
    uvicorn.run(app, host=HOST, port=PORT)
