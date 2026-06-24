# -*- coding: utf-8 -*-
"""
Agent 核心模块 - LLM 提示词优化与图像生成调度
工单编号：人工智能NLP-Agent数字人项目-文生图智能体任务
"""
import json
import re
from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, IMAGE_PROMPT_SYSTEM, DEFAULT_NEGATIVE_PROMPT


def get_llm_client():
    """获取 LLM 客户端"""
    return OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )


def generate_image_prompts(user_description: str) -> dict:
    """
    使用 LLM 优化用户的图像描述，生成多视角提示词
    
    Args:
        user_description: 用户的面部图像描述或生成需求
    Returns:
        dict 包含 facial_features, prompts, negative_prompt
    """
    client = get_llm_client()
    
    messages = [
        {"role": "system", "content": IMAGE_PROMPT_SYSTEM},
        {"role": "user", "content": user_description},
    ]
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )
    
    text = response.choices[0].message.content.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        result = json.loads(text)
        return result
    except json.JSONDecodeError:
        # 降级方案：直接返回用户输入作为提示词
        return {
            "facial_features": user_description,
            "prompts": {
                "straight": user_description,
                "turn_left": f"portrait of a person, turn left 30 degrees, {user_description}",
                "turn_right": f"portrait of a person, turn right 30 degrees, {user_description}",
                "outpainting": f"wide angle portrait, {user_description}"
            },
            "negative_prompt": DEFAULT_NEGATIVE_PROMPT
        }


def analyze_user_intent(user_input: str) -> dict:
    """
    分析用户意图：是描述面部图像，还是指定生成需求
    
    Args:
        user_input: 用户输入
    Returns:
        dict 包含 action 和参数
    """
    client = get_llm_client()
    
    system_prompt = """你是一个图像生成需求分析助手。分析用户的输入，判断他们的需求类型。

【输出格式】返回 JSON：
1. 面部多角度生成（给一张脸，生成多视角）：
{"action": "multi_view", "description": "面部描述"}

2. 文生图（文字描述生成图片）：
{"action": "text_to_image", "description": "图片描述"}

3. 扩图（扩展已有图像）：
{"action": "outpaint", "description": "扩图需求"}

4. 不明确：
{"action": "guide", "guide_text": "引导用户的话"}

请只输出 JSON。"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=300,
    )
    
    text = response.choices[0].message.content.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"action": "guide", "guide_text": "请描述你想生成的图片，或者提供面部图像描述。例如：'帮我生成一张女孩面部的多角度图像'"}


def generate_reply(intent: dict) -> str:
    """生成用户回复"""
    action = intent.get("action", "")
    
    if action == "multi_view":
        return "好的！我来为你生成面部的多角度图像。正在优化提示词并生成图像，请稍候..."
    elif action == "text_to_image":
        return "收到！正在为你生成图片，请稍候..."
    elif action == "outpaint":
        return "收到！正在处理扩图请求，请稍候..."
    elif action == "guide":
        return intent.get("guide_text", "请描述你想生成的图片内容。")
    else:
        return "收到！正在处理你的请求..."


def format_generation_result(prompts_info: dict, generated_files: dict) -> str:
    """格式化生成结果"""
    lines = ["✅ 图像生成完成！"]
    
    if "facial_features" in prompts_info:
        lines.append(f"\n📋 面部特征: {prompts_info['facial_features'][:100]}...")
    
    label_map = {
        "straight": "📸 正面视角",
        "turn_left": "📸 左转30度",
        "turn_right": "📸 右转30度",
        "outpainting": "🖼️ 扩图版本"
    }
    
    for key, label in label_map.items():
        if key in generated_files and generated_files[key]:
            lines.append(f"\n{label}: {generated_files[key]}")
        elif key in prompts_info.get("prompts", {}):
            lines.append(f"\n{label}: [提示词已生成，待图像API调用]")
            lines.append(f"  提示词: {prompts_info['prompts'][key][:80]}...")
    
    return "\n".join(lines)
