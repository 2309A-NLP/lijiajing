# -*- coding: utf-8 -*-
# 工单编号：人工智能NLP-Agent数字人项目-医疗智能体-挂号管理
"""
健康助理 Agent — 挂号管理
Tab1: 对话挂号（NL2SQL）
Tab2: 调用信息（查看最近一次 SQL 生成详情）
"""
import os, json, time
import gradio as gr
from agent import process

_last = {}

# ── 演示用户（真实场景应对接登录）─────────────────────────────────────────────
DEMO_USER_ID = 1
DEMO_USER    = "李明（大宝/二宝父母）"


def chat(user_input: str, history: list):
    if not user_input.strip():
        return history, ""
    t0 = time.time()
    result = process(user_input, DEMO_USER_ID)
    ms = int((time.time() - t0) * 1000)
    _last.update({**result, "cost_ms": ms, "ts": time.strftime("%H:%M:%S")})

    history = history + [{"role": "user", "content": user_input},
                         {"role": "assistant", "content": result["reply"]}]
    sql_md = f"```sql\n{result['sql']}\n```" if result.get("sql") else "（无SQL）"
    return history, sql_md


def get_info():
    if not _last:
        return "请先在对话栏提问"
    rows = _last.get("rows") or []
    return f"""## 最近一次调用（{_last.get('ts','')}）
- **意图**：`{_last.get('intent')}`  耗时 {_last.get('cost_ms')} ms
- **生成SQL**：
```sql
{_last.get('sql') or '无'}
```
- **查询结果**（前5条，共{len(rows)}条）：
```json
{json.dumps(rows[:5], ensure_ascii=False, indent=2)}
```
- **回复**：{_last.get('reply','')}
"""


def build_ui():
    with gr.Blocks(title="健康助理Agent - 挂号管理") as demo:
        gr.Markdown(f"# 🏥 健康助理 Agent — 挂号管理\n当前用户：**{DEMO_USER}**（user_id={DEMO_USER_ID}）")
        with gr.Tabs():
            with gr.TabItem("💬 对话挂号"):
                chatbot = gr.Chatbot(height=400, type="messages", label="对话记录")
                with gr.Row():
                    inp = gr.Textbox(placeholder="例：帮我大宝挂一个今天下午儿科专家的号", scale=5)
                    btn = gr.Button("发送", variant="primary", scale=1)
                sql_box = gr.Markdown(label="生成的SQL")
                gr.Examples(
                    examples=[
                        ["帮我大宝挂一个今天下午2点儿科专家的号"],
                        ["牙科最近的号哪天的？"],
                        ["我之前挂过眼科的一个专家，帮我再约那个专家的号"],
                        ["我明天上午9点想带二宝看皮肤科，还有号吗？"],
                        ["取消我上周三挂的消化内科普通号"],
                        ["帮我查下张建国医生下周的坐诊时间"],
                    ],
                    inputs=inp,
                )
                btn.click(chat, [inp, chatbot], [chatbot, sql_box])
                inp.submit(chat, [inp, chatbot], [chatbot, sql_box])

            with gr.TabItem("📊 调用信息"):
                info_btn = gr.Button("🔄 刷新")
                info_md  = gr.Markdown("点击上方按钮查看")
                info_btn.click(get_info, outputs=info_md)

    return demo


if __name__ == "__main__":
    # 检查数据库
    from config import DB_PATH
    if not os.path.exists(DB_PATH):
        print("初始化数据库...")
        import subprocess, sys
        subprocess.run([sys.executable, "data/init_db.py"], cwd=os.path.dirname(__file__))
    build_ui().launch(server_port=7860, inbrowser=True)
