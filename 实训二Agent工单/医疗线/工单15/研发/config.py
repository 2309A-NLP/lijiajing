# -*- coding: utf-8 -*-
"""
work_order_15 语音识别 - 配置文件
工单编号：人工智能NLP-Agent数字人项目-15-实时语音识别、翻译与会议纪要
"""
import os

# 通义听悟 API 配置
TINGWU_APP_KEY = os.getenv("TINGWU_APP_KEY", "")
TINGWU_AK = os.getenv("TINGWU_AK", "")
TINGWU_SK = os.getenv("TINGWU_SK", "")

# WebSocket 实时识别配置
WS_URL = "wss://tingwu.cn-shanghai.aliyuncs.com/ws/v1"

# 回调 URL 配置
CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:8015/callback")

# 服务配置
HOST = "0.0.0.0"
PORT = 8015
