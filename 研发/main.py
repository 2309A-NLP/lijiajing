# ============================================
# DeepRole v9.0 - AI角色扮演对话系统
# 技术栈：FastAPI + Milvus + Redis + MySQL + DeepSeek
# 核心功能：多路召回 + RRF融合 + BGE-Reranker + 流式输出
# ============================================

# ========== 第一部分：依赖导入 ==========
import json
from fastapi.responses import StreamingResponse  # SSE流式响应
from FlagEmbedding import FlagReranker  # BGE重排序模型
import uuid, redis, asyncio, requests, hashlib, os, webbrowser
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np, pymysql
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

# 多路召回模块（4个检索通道）
from multi_recall import multi_path_search
# 查询改写模块（用DeepSeek优化检索语句）
from rewrite_query import rewrite_query
# 查询扩写模块（生成多角度查询）
from query_expand import expand_query
# 互联网搜索模块（DuckDuckGo实时搜索）
from web_search import search_web
# 后处理校验模块（安全过滤、角色一致性）
from post_check import validate_response
# 对话摘要模块（长对话压缩）
from summary_history import summarize_history

# ========== 第二部分：系统配置 ==========
# MySQL配置（用户、收藏、历史记录）
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "rag_system",
    "charset": "utf8mb4"
}

# Milvus配置（向量数据库）
MILVUS_CONFIG = {
    "host": "127.0.0.1",
    "port": "19530"
}

# BGE-M3向量模型路径（用于语义编码）
BGE_MODEL_PATH = r"D:\2309A nlp 上课软件\BGE-m3\bge-m3"

# DeepSeek大模型配置（对话生成）
LLM_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-33ce819258ee47c19b6c1b6ec6f646fb"),
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "model": "deepseek-chat"
}

# 前端页面模板目录
TEMPLATE_DIR = r"D:\rag_roleplay_system\templates"

BASE_URL = "https://3fbcde3e.r29.cpolar.top"  # 分享链接的基础域名
# ========== 配置结束 ==========


# ========== 第三部分：系统自检 ==========
def self_check():
    """启动前检查所有依赖服务是否正常"""
    print("\n" + "=" * 50)
    print("🔍 系统自检")
    print("=" * 50)

    # 1. 检查MySQL
    try:
        c = pymysql.connect(host=MYSQL_CONFIG["host"], port=MYSQL_CONFIG["port"],
                            user=MYSQL_CONFIG["user"], password=MYSQL_CONFIG["password"],
                            charset="utf8mb4")
        c.close()
        print("✅ [1/5] MySQL 正常")
    except Exception as e:
        print(f"❌ [1/5] MySQL 失败:{e}")

    # 2. 检查Redis
    try:
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=3)
        r.ping()
        print("✅ [2/5] Redis 正常")
    except:
        print("⚠️ [2/5] Redis 不可用")

    # 3. 检查Milvus
    try:
        connections.connect(host=MILVUS_CONFIG["host"], port=MILVUS_CONFIG["port"])
        print("✅ [3/5] Milvus 正常")
    except:
        print("⚠️ [3/5] Milvus 不可用")

    # 4. 检查BGE-M3模型（只检查路径，不实际加载）
    try:
        import os
        if os.path.exists(BGE_MODEL_PATH):
            print("✅ [4/5] BGE-M3 路径正常")
        else:
            print(f"❌ [4/5] BGE-M3 路径不存在:{BGE_MODEL_PATH}")
    except Exception as e:
        print(f"❌ [4/5] BGE-M3 检查失败:{e}")
    # 5. 检查DeepSeek API
    if LLM_CONFIG.get("api_key") and "sk-" in LLM_CONFIG["api_key"]:
        try:
            r = requests.get("https://api.deepseek.com/v1/models",
                             headers={"Authorization": "Bearer " + LLM_CONFIG["api_key"]},
                             timeout=5)
            if r.status_code == 200:
                print("✅ [5/5] DeepSeek API 正常")
            else:
                print(f"⚠️ [5/5] API状态码:{r.status_code}（不影响启动）")
        except Exception as e:
            print(f"⚠️ [5/5] API连接失败:{e}（不影响启动）")
    else:
        print("⚠️ [5/5] API Key未配置")

    print("=" * 50 + "\n")


# 自检已移至 startup_event 执行


# ========== 第四部分：数据库初始化 ==========
def init_db():
    """初始化MySQL表结构"""
    # 创建数据库（如果不存在）
    try:
        c = pymysql.connect(host=MYSQL_CONFIG["host"], port=MYSQL_CONFIG["port"],
                            user=MYSQL_CONFIG["user"], password=MYSQL_CONFIG["password"],
                            charset="utf8mb4")
        cur = c.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS rag_system CHARACTER SET utf8mb4")
        cur.close()
        c.close()
    except Exception as e:
        print(f"⚠️ 创建数据库失败:{e}")

    # 创建表结构
    try:
        c = pymysql.connect(**MYSQL_CONFIG)
        cur = c.cursor()

        # 用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 分享链接表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shares(
                id INT AUTO_INCREMENT PRIMARY KEY,
                share_code VARCHAR(20) UNIQUE NOT NULL,
                owner_username VARCHAR(50) NOT NULL,
                role_type VARCHAR(20) NOT NULL,
                title VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active TINYINT DEFAULT 1
            )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 对话日志表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs(
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50),
                share_code VARCHAR(20),
                role_type VARCHAR(20) NOT NULL,
                persona VARCHAR(20),
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                engine VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 收藏表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favorites(
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                role_type VARCHAR(20),
                persona VARCHAR(20),
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 添加扩展字段（如果不存在）
        try:
            cur.execute("ALTER TABLE users ADD COLUMN profile_json TEXT")
        except:
            pass
        try:
            cur.execute("ALTER TABLE chat_logs ADD COLUMN persona VARCHAR(20) DEFAULT ''")
        except:
            pass
        try:
            cur.execute("ALTER TABLE favorites ADD COLUMN persona VARCHAR(20) DEFAULT ''")
        except:
            pass

        c.commit()
        cur.close()
        c.close()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败:{e}")


# 数据库初始化已移至 startup_event 执行


# ========== 第五部分：Milvus向量数据库初始化（移至startup event） ==========
milvus_col = None  # 全局变量，startup时初始化



# ========== 第六部分：对话记忆管理器（Redis） ==========
class MemMgr:
    """对话历史管理，使用Redis存储，自动过期"""

    def __init__(self):
        try:
            self.r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=3)
            self.r.ping()
            self.ok = True
        except:
            self.r = {}
            self.ok = False

    def save(self, k, role, content):
        """保存一条对话记录"""
        m = json.dumps({"role": role, "content": content, "time": datetime.now().isoformat()}, ensure_ascii=False)
        if self.ok:
            self.r.rpush(k, m)
            self.r.expire(k, 86400)  # 24小时过期
            self.r.ltrim(k, -100, -1)  # 只保留最近100条
        else:
            # 降级到内存存储
            if k not in self.r:
                self.r[k] = []
            self.r[k].append(json.loads(m))
            self.r[k] = self.r[k][-100:]

    def get(self, k, limit=20):
        """获取最近limit条对话历史"""
        if self.ok:
            return [json.loads(m) for m in self.r.lrange(k, -limit, -1)]
        return self.r.get(k, [])[-limit:]


mem = MemMgr()


# ========== 第七部分：检索器（BGE-M3 + Reranker） ==========
class Retriever:
    """
    检索器类
    功能：向量检索 + BGE-Reranker重排序
    优化：模型懒加载（首次使用时才加载，加快启动速度）
    """

    def __init__(self, model_path):
        self.model_path = model_path
        self._model = None  # 懒加载，初始为None
        self._reranker = None

        # 重排序模型较小，启动时加载
        try:
            from FlagEmbedding import FlagReranker
            self._reranker = FlagReranker(r'D:\2309A nlp 上课软件\bge-reranker-v2-m3', use_fp16=True)
            print("✅ BGE-Reranker 加载成功")
        except Exception as e:
            print(f"⚠️ BGE-Reranker 加载失败: {e}")

    @property
    def model(self):
        """懒加载：首次使用时才加载BGE-M3（约1.5GB）"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print("🔄 首次使用，加载 BGE-M3 模型...")
            self._model = SentenceTransformer(self.model_path)
            print("✅ BGE-M3 模型加载成功")
        return self._model

    def search(self, q, role, top_k=3):
        """
        向量检索 + 重排序
        流程：编码查询 → Milvus检索 → Reranker重排 → 去重返回
        """
        results = []
        if milvus_col:
            try:
                model = self.model  # 触发懒加载
                # 1. 将查询文本编码为向量
                qv = model.encode([q], normalize_embeddings=True)[0]

                # 2. 构建过滤条件（按角色筛选）
                expr = None
                if role and role != "虚拟朋友":
                    expr = f'role_type == "{role}"'

                # 3. Milvus向量检索（返回top_k*2条，为重排序留出空间）
                sr = milvus_col.search(
                    data=[qv.tolist()],
                    anns_field="embedding",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=top_k * 2,
                    expr=expr,
                    output_fields=["role_type", "text"]
                )

                # 4. 提取检索结果
                for hit in sr[0]:
                    results.append({
                        "text": hit.entity.get("text"),
                        "score": float(hit.score)  # 余弦相似度得分
                    })

                # 5. BGE-Reranker重排序（交叉编码，比向量相似度更精准）
                if self._reranker and len(results) > 1:
                    pairs = [[q, r["text"]] for r in results]
                    scores = self._reranker.compute_score(pairs)
                    for i, r in enumerate(results):
                        r["score"] = float(scores[i])
                    results.sort(key=lambda x: x["score"], reverse=True)

            except Exception as e:
                print(f"检索失败: {e}")

        # 6. 去重返回
        seen = set()
        uniq = []
        for r in results[:top_k]:
            if r["text"] not in seen:
                uniq.append(r["text"])
                seen.add(r["text"])
        return uniq if uniq else ["暂无相关知识"]


retriever = Retriever(BGE_MODEL_PATH)


# ========== 第八部分：AI对话生成器 ==========
class AIGen:
    """大模型对话生成器，调用DeepSeek API"""

    # 5种角色的专业背景描述
    ROLE_DESC = {
        "虚拟朋友": "你是一个虚拟朋友，擅长日常聊天、情感陪伴、生活建议。",
        "心理医生": "你是一位专业心理医生，精通CBT疗法、情绪管理、压力疏导。",
        "律师": "你是一位资深律师，精通民法、刑法、合同法、劳动法。",
        "投资分析师": "你是一位证券分析师，擅长技术分析、基本面分析、风险管理。",
        "奶茶师": "你是一位奶茶店老板，精通所有奶茶配方和饮品制作。"
    }

    # 3种人格的风格定义
    PERSONA = {
        "默认": "说话自然、友好、平衡。",
        "暴躁老哥": """【必须严格遵守】你现在是东北暴躁大哥人格，无论扮演什么角色都必须用暴躁语气：
            - 口头禅：'你大爷的'、'老子'、'搁这'、'啥玩意儿'、'别磨叽'
            - 语气冲但心眼好，骂完立刻给甜枣
            - 动作描写：'（拍桌）''（瞪眼）''（叹气）'
            - 禁止温柔词汇，禁止说'亲爱的''慢慢来''抱抱你'""",
        "知性姐姐": """【必须严格遵守】你现在是温柔知性姐姐人格，无论扮演什么角色都必须用温柔语气：
            - 口头禅：'亲爱的'、'慢慢来'、'不急的'、'我懂你'、'抱抱你'
            - 温柔语气+小表情：'🌸''💕''🍀'
            - 先肯定再建议
            - 禁止粗鲁词汇，禁止说'你大爷的''老子''搁这'"""
    }

    @staticmethod
    async def gen(role, q, hist, kb, persona="默认", profile=None):
        """生成回复，优先使用LLM，失败时降级到规则引擎"""
        if LLM_CONFIG.get("api_key") and "sk-" in LLM_CONFIG["api_key"]:
            try:
                return await AIGen._llm(role, q, hist, kb, persona, profile), "llm"
            except Exception as e:
                print(f"  ⚠️ LLM失败:{e}")
        # 降级规则
        await asyncio.sleep(0.1)
        return AIGen._rule(role, q), "rule"

    @staticmethod
    async def _llm(role, q, hist, kb, persona, profile=None):
        """调用DeepSeek API生成回复"""
        rd = AIGen.ROLE_DESC.get(role, AIGen.ROLE_DESC["虚拟朋友"])
        pd = AIGen.PERSONA.get(persona, AIGen.PERSONA["默认"])

        # 解析用户资料
        profile_info = json.loads(profile) if profile and profile != 'null' else {}
        pi = ''
        if profile_info.get('name'): pi += f"用户叫{profile_info['name']}。"
        if profile_info.get('gender'): pi += f"性别{profile_info['gender']}。"
        if profile_info.get('birth'): pi += f"生日{profile_info['birth']}。"
        if profile_info.get('interest'): pi += f"兴趣爱好{profile_info['interest']}。"

        # 构建系统提示词
        sp = f"【重要指令】\n1. 用户资料：{pi if pi else '暂无'}\n2. 必须用用户资料中的名字称呼用户，绝对不要问用户叫什么名字。\n3. 严格按照以下人格设定回答：\n{rd}\n{pd}\n4. 如果知识库有相关内容，请详细回答。\n5. 【排版要求】回复中适当使用换行、数字列表、重点加粗，让内容层次分明，便于阅读。"
        # 构建消息列表
        ms = [{"role": "system", "content": sp}]
        for h in hist[-6:]:
            ms.append({"role": "user" if h["role"] == "user" else "assistant", "content": h["content"]})
        if kb and kb[0] != "暂无相关知识":
            ms.append({"role": "system", "content": "参考:\n" + "\n".join(kb[:3])})
        ms.append({"role": "user", "content": q})

        # 调用DeepSeek API
        r = requests.post(
            LLM_CONFIG["api_url"],
            headers={"Authorization": "Bearer " + LLM_CONFIG["api_key"], "Content-Type": "application/json"},
            json={"model": LLM_CONFIG["model"], "messages": ms, "temperature": 1.0, "max_tokens": 800},
            timeout=25
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        raise Exception(f"API:{r.status_code}")

    @staticmethod
    async def gen_options(role, last_response, persona="默认"):
        """根据AI回复，动态生成3个追问选项"""
        if LLM_CONFIG.get("api_key") and "sk-" in LLM_CONFIG["api_key"]:
            rd = AIGen.ROLE_DESC.get(role, AIGen.ROLE_DESC["虚拟朋友"])
            pd = AIGen.PERSONA.get(persona, AIGen.PERSONA["默认"])
            sp = f"{rd}\n{pd}\n你刚才对用户说了这段话：'{last_response}'\n根据你刚才说的内容，生成3个用户可能会回复的简短回答选项（每个15字以内），用换行分隔，不要编号。"
            try:
                r = requests.post(
                    LLM_CONFIG["api_url"],
                    headers={"Authorization": "Bearer " + LLM_CONFIG["api_key"], "Content-Type": "application/json"},
                    json={"model": LLM_CONFIG["model"], "messages": [{"role": "system", "content": sp}],
                          "temperature": 0.8, "max_tokens": 100},
                    timeout=15
                )
                if r.status_code == 200:
                    txt = r.json()["choices"][0]["message"]["content"].strip()
                    opts = [o.strip() for o in txt.split("\n") if o.strip()][:3]
                    if len(opts) >= 3:
                        return opts
            except:
                pass
        return ["能再详细说说吗？", "然后呢？", "后来怎么样了？"]

    @staticmethod
    def _rule(role, q):
        """规则引擎降级方案"""
        rr = {
            "虚拟朋友": {"心情": "听到你心情不好，我在呢。", "default": "嗯嗯我懂！"},
            "心理医生": {"失眠": "失眠确实困扰人。", "default": "嗯我在听。"},
            "律师": {"劳动": "这涉及劳动争议。", "default": "请描述。"},
            "投资分析师": {"风险": "注意风险控制。", "default": "投资需谨慎。"},
            "奶茶师": {"珍珠": "珍珠奶茶是招牌！", "default": "欢迎光临！"}
        }
        r = rr.get(role, rr["虚拟朋友"])
        for k, v in r.items():
            if k in q:
                return v
        return r.get("default", "请继续。")


# ========== 第九部分：FastAPI应用初始化 ==========
app = FastAPI(title="DeepRole v9.0")


# 请求模型
class CR(BaseModel):
    profile: Optional[str] = None
    username: str = "guest"
    role_type: str = "虚拟朋友"
    message: str
    share_code: Optional[str] = None
    persona: str = "默认"


# 安全关键词检测
CRISIS_KW = ["自杀", "跳楼", "想死", "自残", "割腕", "不想活"]


# ========== 第十部分：流式对话接口（核心） ==========
@app.post("/chat/stream")
async def chat_stream(req: CR):
    """
    流式对话接口 - 使用SSE协议逐字输出
    流程：安全检测 → 查询改写 → 查询扩写 → 多路召回 → 构建提示词 → 流式生成 → 后处理校验
    """
    # 1. 安全检测（危机关键词拦截）
    if any(k in req.message for k in CRISIS_KW):
        async def safety_stream():
            data = json.dumps({"response": "【⚠️ 安全提醒】\n请拨打心理援助热线:400-161-9995", "done": True},
                              ensure_ascii=False)
            yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(safety_stream(), media_type="text/event-stream")

    # 2. 获取对话历史
    mk = "chat:" + req.username + ":" + req.role_type
    hist = mem.get(mk, 10)

    # 3. 获取用户资料（用于个性化检索和称呼）
    profile_info = json.loads(req.profile) if req.profile and req.profile != 'null' else {}
    user_name = profile_info.get('name', '')

    # 4. 查询改写（用DeepSeek优化检索语句）
    if user_name:
        enhanced_message = f"{req.message} 我是{user_name}"
    else:
        enhanced_message = req.message

    try:
        rewritten_queries = rewrite_query(enhanced_message, req.persona, req.role_type)
        main_query = rewritten_queries[0] if rewritten_queries else enhanced_message
    except:
        main_query = enhanced_message

    # 5. 查询扩写（生成多角度查询，提高召回率）
    try:
        expanded_queries = expand_query(main_query, req.role_type, req.persona)
    except:
        expanded_queries = [main_query]

    # 6. 多路召回（对每个扩写查询执行检索）
    all_results = []
    for eq in expanded_queries[:3]:
        kb_results = multi_path_search(eq, req.role_type, top_k=3)
        all_results.extend(kb_results)

    # 7. 去重合并
    seen = set()
    kb_results = []
    for r in all_results:
        key = r["text"][:100]
        if key not in seen:
            seen.add(key)
            kb_results.append(r)

    kb = [r["text"] for r in kb_results[:3]]

    # 8. 互联网搜索补充
    try:
        web_results = search_web(main_query, num=1)
        for wr in web_results:
            if wr.get("text"):
                kb.append(wr.get("text"))
        print(f"  🌐 互联网: {len(web_results)}条")
    except Exception as e:
        print(f"  ⚠️ 互联网搜索失败: {e}")

    # 9. 保存用户消息到历史
    mem.save(mk, "user", req.message)

    # 10. 构建系统提示词
    rd = AIGen.ROLE_DESC.get(req.role_type, AIGen.ROLE_DESC["虚拟朋友"])
    pd = AIGen.PERSONA.get(req.persona, AIGen.PERSONA["默认"])
    profile_info = json.loads(req.profile) if req.profile and req.profile != 'null' else {}
    pi = ''
    if profile_info.get('name'): pi += f"用户叫{profile_info['name']}。"
    if profile_info.get('gender'): pi += f"性别{profile_info['gender']}。"
    if profile_info.get('birth'): pi += f"生日{profile_info['birth']}。"
    if profile_info.get('interest'): pi += f"兴趣爱好{profile_info['interest']}。"
    sp = f"【重要指令】{'用户资料：' + pi if pi else ''}严格按照以下人格设定回答：\n{rd}\n{pd}\n请详细、自然地回答用户问题。"

    # 11. 构建消息列表
    ms = [{"role": "system", "content": sp}]
    for h in hist[-6:]:
        ms.append({"role": "user" if h["role"] == "user" else "assistant", "content": h["content"]})
    if kb and kb[0] != "暂无相关知识":
        ms.append({"role": "system", "content": "参考:\n" + "\n".join(kb[:3])})
    ms.append({"role": "user", "content": req.message})

    # 12. 流式生成器（边接收边输出）
    async def generate_stream():
        full_response = ""
        try:
            # 调用DeepSeek流式API
            resp = requests.post(
                LLM_CONFIG["api_url"],
                headers={"Authorization": "Bearer " + LLM_CONFIG["api_key"], "Content-Type": "application/json"},
                json={"model": LLM_CONFIG["model"], "messages": ms, "temperature": 1.0, "max_tokens": 500,
                      "stream": True},
                stream=True,
                timeout=60
            )
            # 边接收边输出（真正的流式）
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                full_response += content
                                yield f"data: {json.dumps({'chunk': content}, ensure_ascii=False)}\n\n"
                                await asyncio.sleep(0)
                        except json.JSONDecodeError:
                            pass

            # 13. 后处理校验（安全过滤）
            try:
                full_response = validate_response(full_response, req.role_type, req.persona)
            except:
                pass

            # 14. 生成追问选项
            follow_options = await AIGen.gen_options(req.role_type, full_response, req.persona)

            # 15. 发送完成标记
            yield f"data: {json.dumps({'done': True, 'full_response': full_response, 'retrieved_knowledge': kb, 'engine': 'llm', 'follow_options': follow_options}, ensure_ascii=False)}\n\n"

            # 16. 保存AI回复到历史
            mem.save(mk, "assistant", full_response)

            # 17. 保存对话日志到MySQL
            try:
                c = pymysql.connect(**MYSQL_CONFIG)
                cur = c.cursor()
                cur.execute(
                    "INSERT INTO chat_logs(username,share_code,role_type,persona,message,response,engine) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (req.username, req.share_code, req.role_type, req.persona, req.message, full_response, "llm")
                )
                c.commit()
                c.close()
            except:
                pass

        except Exception as e:
            # 降级处理
            print(f"❌ 流式调用失败: {e}")
            full_response = AIGen._rule(req.role_type, req.message)
            yield f"data: {json.dumps({'chunk': full_response}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'full_response': full_response, 'retrieved_knowledge': kb, 'engine': 'rule'}, ensure_ascii=False)}\n\n"
            mem.save(mk, "assistant", full_response)

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


# ========== 第十一部分：用户认证接口 ==========
@app.post("/api/register")
async def reg(u: str, p: str):
    """用户注册"""
    u = u.strip()
    if len(u) < 2 or len(p) < 2:
        return {"ok": False, "msg": "至少2个字符"}
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    try:
        cur.execute("INSERT INTO users(username,password_hash,profile_json) VALUES(%s,%s,%s)",
                    (u, hashlib.sha256(p.encode()).hexdigest(), "{}"))
        c.commit()
        return {"ok": True, "msg": "注册成功"}
    except:
        cur.execute("SELECT id FROM users WHERE username=%s", (u,))
        exists = cur.fetchone() is not None
        return {"ok": True, "msg": "用户已存在"} if exists else {"ok": False}
    finally:
        c.close()


@app.post("/api/login")
async def login(u: str, p: str):
    """用户登录，返回用户资料"""
    u = u.strip()
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT password_hash, profile_json FROM users WHERE username=%s", (u,))
    row = cur.fetchone()
    if row and row[0] == hashlib.sha256(p.encode()).hexdigest():
        cur.execute("UPDATE users SET last_login=NOW() WHERE username=%s", (u,))
        c.commit()
        profile = row[1] if row[1] else "{}"
        c.close()
        return {"ok": True, "msg": "登录成功", "profile": profile}
    c.close()
    return {"ok": False, "msg": "用户名或密码错误"}


# ========== 第十二部分：用户资料接口 ==========
@app.get("/api/profile")
async def get_profile(u: str):
    """获取用户资料"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT profile_json FROM users WHERE username=%s", (u,))
    row = cur.fetchone()
    c.close()
    if row and row[0]:
        return {"ok": True, "profile": json.loads(row[0])}
    return {"ok": True, "profile": {}}


@app.post("/api/save_profile")
async def save_profile_api(u: str, p: str = "{}"):
    """保存用户资料到MySQL"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("UPDATE users SET profile_json=%s WHERE username=%s", (p, u))
    c.commit()
    c.close()
    return {"ok": True}


# ========== 第十三部分：历史记录和收藏接口 ==========
@app.get("/api/history")
async def api_history(u: str, rt: str = None):
    """获取对话历史"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    if rt:
        cur.execute(
            "SELECT role_type,message,response,created_at FROM chat_logs WHERE username=%s AND role_type=%s ORDER BY created_at DESC LIMIT 50",
            (u, rt))
    else:
        cur.execute(
            "SELECT role_type,message,response,created_at FROM chat_logs WHERE username=%s ORDER BY created_at DESC LIMIT 50",
            (u,))
    rows = cur.fetchall()
    c.close()
    return [{"role": r[0], "q": r[1], "a": r[2], "time": str(r[3])} for r in rows]


@app.get("/api/favorites")
async def get_favorites(u: str):
    """获取收藏列表"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute(
        "SELECT role_type,persona,question,answer,created_at FROM favorites WHERE username=%s ORDER BY created_at DESC LIMIT 50",
        (u,))
    rows = cur.fetchall()
    c.close()
    return [{"role": r[0], "persona": r[1], "q": r[2], "a": r[3], "time": str(r[4])} for r in rows]


@app.post("/api/favorite")
async def add_favorite(u: str, rt: str = "", p: str = "", q: str = "", a: str = ""):
    """添加收藏"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("INSERT INTO favorites(username,role_type,persona,question,answer) VALUES(%s,%s,%s,%s,%s)",
                (u, rt, p, q, a))
    c.commit()
    c.close()
    return {"ok": True}


@app.delete("/api/favorite")
async def del_favorite(u: str, q: str = ""):
    """删除收藏"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("DELETE FROM favorites WHERE username=%s AND question=%s LIMIT 1", (u, q))
    c.commit()
    c.close()
    return {"ok": True}


# ========== 第十四部分：统计和成就接口 ==========
@app.get("/api/my_stats")
async def my_stats(u: str):
    """获取用户统计数据"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM chat_logs WHERE username=%s", (u,))
    total = cur.fetchone()[0]
    cur.execute(
        "SELECT role_type, COUNT(*) as cnt FROM chat_logs WHERE username=%s GROUP BY role_type ORDER BY cnt DESC LIMIT 1",
        (u,))
    row = cur.fetchone()
    cur.execute(
        "SELECT role_type, COUNT(*) as cnt FROM chat_logs WHERE username=%s GROUP BY role_type ORDER BY cnt DESC", (u,))
    rd = cur.fetchall()
    cur.execute(
        "SELECT persona, COUNT(*) as cnt FROM chat_logs WHERE username=%s AND persona!='' GROUP BY persona ORDER BY cnt DESC",
        (u,))
    pd = cur.fetchall()
    c.close()
    return {
        "total": total,
        "fav": row[0] if row else "-",
        "roleDist": [{"role": r[0], "cnt": r[1]} for r in rd],
        "personaDist": [{"persona": r[0], "cnt": r[1]} for r in pd]
    }


@app.get("/api/achievements")
async def get_achievements(u: str):
    """获取成就徽章"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM chat_logs WHERE username=%s", (u,))
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM favorites WHERE username=%s", (u,))
    favs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM shares WHERE owner_username=%s", (u,))
    shares = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT role_type) FROM chat_logs WHERE username=%s", (u,))
    roles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT persona) FROM chat_logs WHERE username=%s AND persona!=''", (u,))
    personas = cur.fetchone()[0]
    c.close()

    # 成就列表
    achievements = [
        {"name": "初来乍到", "desc": "发送第一条消息", "icon": "👶", "unlock": total >= 1, "color": "#4f46e5"},
        {"name": "话痨新人", "desc": "发送10条消息", "icon": "💬", "unlock": total >= 10, "color": "#059669"},
        {"name": "聊天达人", "desc": "发送50条消息", "icon": "🎯", "unlock": total >= 50, "color": "#d97706"},
        {"name": "百话王", "desc": "发送100条消息", "icon": "👑", "unlock": total >= 100, "color": "#dc2626"},
        {"name": "千言万语", "desc": "发送500条消息", "icon": "🏆", "unlock": total >= 500, "color": "#7c3aed"},
        {"name": "收藏家", "desc": "收藏5条对话", "icon": "⭐", "unlock": favs >= 5, "color": "#d97706"},
        {"name": "囤积狂", "desc": "收藏20条对话", "icon": "💎", "unlock": favs >= 20, "color": "#059669"},
        {"name": "分享达人", "desc": "创建3个分享链接", "icon": "🔗", "unlock": shares >= 3, "color": "#4f46e5"},
        {"name": "社交之星", "desc": "创建10个分享链接", "icon": "🌟", "unlock": shares >= 10, "color": "#ec4899"},
        {"name": "探索者", "desc": "使用过3个以上角色", "icon": "🎭", "unlock": roles >= 3, "color": "#0891b2"},
        {"name": "全角色制霸", "desc": "使用过全部5个角色", "icon": "🏅", "unlock": roles >= 5, "color": "#7c3aed"},
        {"name": "人格分裂", "desc": "使用过全部3种人格", "icon": "🎪", "unlock": personas >= 3, "color": "#ec4899"},
    ]
    return achievements

# ============ 金句墙 ============
@app.get("/api/quotes")
async def get_quotes(u: str):
    """获取用户金句墙"""
    key = f"quotes:{u}"
    try:
        quotes = [json.loads(q) for q in mem.r.lrange(key, 0, -1)]
        return {"ok": True, "quotes": list(reversed(quotes))}
    except:
        return {"ok": True, "quotes": []}

@app.post("/api/save_quote")
async def save_quote_api(u: str, role: str = "", persona: str = "", text: str = ""):
    """保存金句"""
    try:
        key = f"quotes:{u}"
        quote = json.dumps({
            "role": role,
            "persona": persona,
            "text": text[:100],
            "time": datetime.now().strftime("%m-%d %H:%M")
        }, ensure_ascii=False)
        mem.r.rpush(key, quote)
        mem.r.ltrim(key, -50, -1)
        mem.r.expire(key, 86400 * 30)
    except:
        pass
    return {"ok": True}

@app.delete("/api/quote")
async def delete_quote(u: str, text: str = ""):
    """删除金句"""
    key = f"quotes:{u}"
    try:
        quotes = [json.loads(q) for q in mem.r.lrange(key, 0, -1)]
        mem.r.delete(key)
        for q in quotes:
            if q.get("text", "")[:50] != text[:50]:
                mem.r.rpush(key, json.dumps(q, ensure_ascii=False))
        mem.r.ltrim(key, -50, -1)
    except:
        pass
    return {"ok": True}
# ========== 分享链接接口 ==========
@app.get("/api/my_shares")
async def my_shares(u: str):
    """获取用户的分享链接列表"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT share_code, role_type, title, created_at FROM shares WHERE owner_username=%s ORDER BY created_at DESC", (u,))
    rows = cur.fetchall()
    res = []
    for r in rows:
        res.append({
            "code": r[0],
            "role": r[1],
            "title": r[2],
            "time": str(r[3]),
            "msgs": 0,
            "url": BASE_URL + "/s/" + r[0]
        })
    c.close()
    return res


@app.get("/api/share_info")
async def share_info(code: str):
    """获取分享链接的信息"""
    c = pymysql.connect(**MYSQL_CONFIG)
    cur = c.cursor()
    cur.execute("SELECT owner_username, role_type, title, is_active FROM shares WHERE share_code=%s", (code,))
    row = cur.fetchone()
    c.close()
    if row and row[3]:
        return {"ok": True, "owner": row[0], "role": row[1], "title": row[2]}
    return {"ok": False}
# ========== 第十五部分：娱乐功能接口 ==========
@app.get("/api/fortune")
async def daily_fortune():
    """每日运势签"""
    import random
    fortunes = [
        ("🌟 大吉", "今天会遇到懂你的人，大胆聊！", "👥 虚拟朋友 × 默认"),
        ("🌈 中吉", "温柔说话会有意想不到的收获～", "🌸 知性姐姐 × 虚拟朋友"),
        ("🔥 小吉", "暴躁一点也无妨，释放压力！", "😤 暴躁老哥 × 律师"),
        ("🍀 末吉", "今天适合安静地喝杯奶茶思考人生", "🧋 奶茶师 × 默认"),
        ("⭐ 吉", "贵人就在身边，多说两句话吧～", "📈 分析师 × 知性姐姐"),
        ("💫 大吉", "幸运值爆表！说什么都有人懂", "👥 虚拟朋友 × 知性姐姐"),
        ("🌙 小吉", "夜晚灵感多，适合深夜聊天", "🦉 心理医生 × 默认"),
        ("🌸 吉", "治愈系能量满分，温柔待人", "🏥 心理医生 × 知性姐姐"),
        ("🔥 大吉", "今天怼天怼地怼空气都对！", "⚖️ 律师 × 暴躁老哥"),
    ]
    fortune = random.choice(fortunes)
    return {"ok": True, "level": fortune[0], "desc": fortune[1], "recommend": fortune[2]}


@app.get("/api/daily_report")
async def daily_report(u: str):
    """日报接口（简化版）"""
    return {"today": 0, "yesterday": 0, "fav_role": "-", "total_favs": 0, "total_shares": 0}


# ========== 第十六部分：前端页面路由 ==========
@app.get("/", response_class=HTMLResponse)
async def home():
    """登录页面"""
    with open(os.path.join(TEMPLATE_DIR, "login.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/splash", response_class=HTMLResponse)
async def splash_page():
    """启动过渡页（人格测试）"""
    with open(os.path.join(TEMPLATE_DIR, "splash.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """主对话页面"""
    with open(os.path.join(TEMPLATE_DIR, "chat.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """数据仪表盘页面"""
    with open(os.path.join(TEMPLATE_DIR, "dashboard.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/favicon.ico")
async def favicon():
    """网站图标"""
    from fastapi.responses import FileResponse
    return FileResponse("templates/favicon.ico")


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    """Chrome开发者工具请求（忽略）"""
    return {"status": "ok"}


# ========== 第十七部分：启动事件（自检+数据库初始化+索引构建） ==========
@app.on_event("startup")
async def startup_event():
    """服务启动时执行：自检、数据库初始化、Milvus连接、BM25索引构建"""
    global milvus_col

    # 1. 系统自检
    self_check()

    # 2. 数据库初始化
    init_db()

    # 3. Milvus连接
    try:
        connections.connect(host=MILVUS_CONFIG["host"], port=MILVUS_CONFIG["port"])
        if not utility.has_collection("knowledge_base"):
            fs = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="role_type", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
            ]
            milvus_col = Collection("knowledge_base", CollectionSchema(fs))
            milvus_col.create_index("embedding", {
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            })
            milvus_col.load()
        else:
            milvus_col = Collection("knowledge_base")
            milvus_col.load()
        print("✅ Milvus 连接成功")
    except Exception as e:
        milvus_col = None
        print(f"⚠️ Milvus 不可用: {e}")

    # 4. BM25索引构建
    try:
        from bm25_search import build_bm25_index_from_kb
        build_bm25_index_from_kb()
    except Exception as e:
        print(f"⚠️ BM25 索引初始化失败: {e}")


# ========== 第十八部分：启动入口 ==========
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 DeepRole v9.0 完整版! 音效+重排序+每日报告\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

