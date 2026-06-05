# app - 主程序模块

## 文件说明
| 文件 | 作用 |
|------|------|
| `main.py` | FastAPI 主程序，包含所有 API 接口和对话核心逻辑 |

## 代码示例
```python
# 启动服务
uvicorn.run(app, host="0.0.0.0", port=8000)

# 流式对话接口
@app.post("/chat/stream")
async def chat_stream(req: CR):
    # 多路召回 + 流式输出
    ...