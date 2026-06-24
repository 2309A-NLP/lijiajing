# -*- coding: utf-8 -*-
"""
图像生成 API 模块
工单编号：人工智能NLP-Agent数字人项目-文生图智能体任务

支持后端：
- siliconflow：通过 SiliconFlow API 调用 FLUX 等模型
- openai：通过 OpenAI DALL-E 3
- local_sd：本地 Stable Diffusion（通过 API 接口）
"""
import os
import time
import base64
from typing import Optional
from config import IMAGE_API_TYPE, IMAGE_API_BASE_URL, IMAGE_API_KEY, IMAGE_MODEL, OUTPUT_DIR


def generate_image(prompt: str, negative_prompt: str = None, 
                   image_url: str = None, size: str = "1024x1024") -> Optional[str]:
    """
    生成图像，返回文件路径
    
    Args:
        prompt: 正向提示词
        negative_prompt: 负面提示词
        image_url: 参考图像URL（用于图生图）
        size: 图像尺寸
    Returns:
        生成的图像本地路径，失败返回 None
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if IMAGE_API_TYPE == "siliconflow":
        return _generate_siliconflow(prompt, negative_prompt, size)
    elif IMAGE_API_TYPE == "openai":
        return _generate_openai(prompt, size)
    elif IMAGE_API_TYPE == "local_sd":
        return _generate_local_sd(prompt, negative_prompt, image_url)
    else:
        print(f"[WARN] 未知的 IMAGE_API_TYPE: {IMAGE_API_TYPE}，使用模拟模式")
        return _generate_mock(prompt)


def _generate_siliconflow(prompt: str, negative_prompt: str = None, 
                          size: str = "1024x1024") -> Optional[str]:
    """通过 SiliconFlow API 生成图像"""
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=IMAGE_API_BASE_URL,
            api_key=IMAGE_API_KEY,
        )
        
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            size=size,
            n=1,
        )
        
        if response.data and response.data[0].url:
            # 下载图片
            import urllib.request
            timestamp = int(time.time())
            filename = f"generated_{timestamp}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            urllib.request.urlretrieve(response.data[0].url, filepath)
            print(f"[Image] 图片已保存: {filepath}")
            return filepath
        else:
            print(f"[Image] API返回无图片数据")
            return None
    except Exception as e:
        print(f"[Image] SiliconFlow API 错误: {e}")
        return None


def _generate_openai(prompt: str, size: str = "1024x1024") -> Optional[str]:
    """通过 OpenAI DALL-E 3 生成图像"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=IMAGE_API_KEY)
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=1,
        )
        
        if response.data and response.data[0].url:
            import urllib.request
            timestamp = int(time.time())
            filename = f"dalle3_{timestamp}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            urllib.request.urlretrieve(response.data[0].url, filepath)
            print(f"[Image] 图片已保存: {filepath}")
            return filepath
        return None
    except Exception as e:
        print(f"[Image] OpenAI DALL-E 3 错误: {e}")
        return None


def _generate_local_sd(prompt: str, negative_prompt: str = None,
                       image_url: str = None) -> Optional[str]:
    """通过本地 Stable Diffusion WebUI API 生成"""
    try:
        import requests
        
        sd_url = os.getenv("SD_API_URL", "http://127.0.0.1:7860")
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "steps": 20,
            "cfg_scale": 7,
            "width": 1024,
            "height": 1024,
        }
        
        if image_url:
            # 图生图模式
            payload["init_images"] = [image_url]
            endpoint = f"{sd_url}/sdapi/v1/img2img"
        else:
            endpoint = f"{sd_url}/sdapi/v1/txt2img"
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get("images"):
            # 解码 base64 图片
            img_data = base64.b64decode(result["images"][0])
            timestamp = int(time.time())
            filename = f"sd_{timestamp}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            print(f"[Image] 图片已保存: {filepath}")
            return filepath
        return None
    except Exception as e:
        print(f"[Image] Local SD API 错误: {e}")
        return None


def _generate_mock(prompt: str) -> Optional[str]:
    """模拟模式：生成占位文件"""
    timestamp = int(time.time())
    filename = f"mock_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"[模拟图像生成]\n提示词: {prompt}\n状态: 需要配置有效的 IMAGE_API_KEY 才能生成真实图片\n")
    print(f"[Image] 模拟模式，占位文件: {filepath}")
    return filepath
