#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文生图智能体 - 主程序入口
工单编号：人工智能NLP-Agent数字人项目-文生图智能体任务

功能：
- 面部多角度图像生成（正面、左转、右转）
- 图像扩图（outpainting）
- 文生图（文字描述生成图片）
- LLM 提示词优化

使用方式：
    python app.py

环境变量：
    LLM_BASE_URL      - LLM API 地址
    LLM_API_KEY       - LLM API Key
    IMAGE_API_TYPE    - 图像后端类型（siliconflow/openai/local_sd/mock）
    IMAGE_API_KEY     - 图像 API Key（默认同 LLM_API_KEY）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import OUTPUT_DIR, DEFAULT_NEGATIVE_PROMPT
from agent import generate_image_prompts, analyze_user_intent, generate_reply, format_generation_result
from image_api import generate_image


def handle_multi_view(description: str) -> str:
    """处理面部多角度生成"""
    # LLM 优化提示词
    prompts_info = generate_image_prompts(description)
    
    generated_files = {}
    prompt_map = prompts_info.get("prompts", {})
    neg = prompts_info.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT)
    
    # 生成4个视角
    for view_key, view_label in [("straight", "正面"), ("turn_left", "左转"), ("turn_right", "右转"), ("outpainting", "扩图")]:
        if view_key in prompt_map:
            print(f"  → 正在生成{view_label}视角...")
            filepath = generate_image(prompt_map[view_key], negative_prompt=neg)
            generated_files[view_key] = filepath
    
    return format_generation_result(prompts_info, generated_files)


def handle_text_to_image(description: str) -> str:
    """处理文生图"""
    print(f"  → 正在根据描述生成图片...")
    filepath = generate_image(description, negative_prompt=DEFAULT_NEGATIVE_PROMPT)
    
    if filepath:
        return f"✅ 图片生成完成！\n保存路径: {filepath}\n提示词: {description[:100]}..."
    else:
        return "❌ 图片生成失败，请检查 API 配置后重试。"


def handle_outpaint(description: str) -> str:
    """处理扩图"""
    print(f"  → 正在处理扩图请求...")
    # 扩图使用更宽的提示词
    outpaint_prompt = f"wide angle, extended background, cinematic composition, {description}"
    filepath = generate_image(outpaint_prompt, negative_prompt=DEFAULT_NEGATIVE_PROMPT)
    
    if filepath:
        return f"✅ 扩图完成！\n保存路径: {filepath}"
    else:
        return "❌ 扩图失败，请检查 API 配置后重试。"


def main():
    """主循环"""
    print("=" * 50)
    print("🎨 欢迎使用文生图智能体！")
    print("=" * 50)
    print("我可以帮你：")
    print("  • 面部多角度生成：描述一个面部图像，生成正面/左转/右转/扩图")
    print("  • 文生图：描述你想要的图片")
    print("  • 扩图：扩展已有图像的背景")
    print("\n示例：")
    print("  '帮我生成一个亚洲女孩的面部多角度图像'")
    print("  '生成一张赛博朋克风格的城市夜景'")
    print("\n图像输出目录:", OUTPUT_DIR)
    print("输入 '退出' 或 'quit' 结束\n")
    
    while True:
        try:
            user_input = input("💬 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见～ 👋")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("退出", "quit", "exit", "q"):
            print("再见～ 👋")
            break
        
        # 分析用户意图
        intent = analyze_user_intent(user_input)
        action = intent.get("action", "")
        
        # 生成初始回复
        print(f"🤖 图像助手：{generate_reply(intent)}")
        
        # 根据意图执行
        if action == "multi_view":
            description = intent.get("description", user_input)
            result = handle_multi_view(description)
            print(f"🤖 图像助手：{result}")
        
        elif action == "text_to_image":
            description = intent.get("description", user_input)
            result = handle_text_to_image(description)
            print(f"🤖 图像助手：{result}")
        
        elif action == "outpaint":
            description = intent.get("description", user_input)
            result = handle_outpaint(description)
            print(f"🤖 图像助手：{result}")
        
        elif action == "guide":
            print(f"🤖 图像助手：{generate_reply(intent)}")
        
        else:
            # 默认：文生图
            result = handle_text_to_image(user_input)
            print(f"🤖 图像助手：{result}")


if __name__ == "__main__":
    main()
