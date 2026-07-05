"""AI陪练服务。

提供语音对话练习功能，支持中英混合对话。
使用 Groq Whisper 进行语音识别，Gemini 进行对话生成，Edge TTS 进行语音合成。
"""
import asyncio
import base64
import logging
import tempfile
import os
from typing import Any

import httpx
import edge_tts

from app.config import settings
from app.services.llm_client import chat_json

log = logging.getLogger(__name__)

# Groq API 配置（免费 Whisper）
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Edge TTS 配置
EDGE_TTS_ENDPOINT = "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list"


async def process_audio(audio_data: str, audio_format: str = "mp3") -> dict[str, Any]:
    """处理音频：语音转文字 + 语言检测。
    
    使用 Groq Whisper 进行语音识别，支持中英文混合识别。
    """
    if not GROQ_API_KEY:
        log.debug("GROQ_API_KEY 未配置，返回模拟数据")
        return {
            "success": True,
            "text": "Hello, I want to practice English with you.",
            "lang": "en"
        }

    try:
        # 准备音频数据
        audio_bytes = base64.b64decode(audio_data)
        
        # 调用 Groq Whisper API
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 使用 multipart/form-data 上传音频
            files = {
                "file": (f"audio.{audio_format}", audio_bytes, f"audio/{audio_format}")
            }
            data = {
                "model": "whisper-large-v3-turbo",
                "response_format": "verbose_json",
                "language": "auto"
            }
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
            
            resp = await client.post(
                f"{GROQ_BASE_URL}/audio/transcriptions",
                files=files,
                data=data,
                headers=headers
            )
            resp.raise_for_status()
            
            result = resp.json()
            text = result.get("text", "").strip()
            language = result.get("language", "en")
            
            # 语言映射
            lang_map = {
                "zh": "zh",
                "zh-cn": "zh",
                "zh-tw": "zh",
                "en": "en",
                "en-us": "en",
                "en-gb": "en",
            }
            lang = lang_map.get(language.lower(), "en")
            
            log.debug("语音识别结果: text=%s, lang=%s", text[:50], lang)
            
            return {
                "success": True,
                "text": text,
                "lang": lang
            }
            
    except httpx.HTTPStatusError as e:
        log.error("Groq API 调用失败: %s", e.response.status_code)
        return {
            "success": False,
            "error": f"语音识别服务调用失败: {e.response.status_code}"
        }
    except Exception as e:
        log.error("语音处理失败: %s", e)
        return {
            "success": False,
            "error": f"语音处理失败: {str(e)}"
        }


async def chat_with_ai(text: str, lang: str, history: list = []) -> dict[str, Any]:
    """与 AI 进行对话。
    
    根据用户输入的语言和内容，AI 会选择：
    1. 如果用户说中文 → 翻译成英文 + 解释
    2. 如果用户说英文 → 回答问题 + 纠正语法
    """
    if not settings.LLM_API_KEY:
        log.debug("LLM_API_KEY 未配置，返回模拟数据")
        is_chinese = lang == "zh"
        if is_chinese:
            reply_text = "好的，让我们用英语对话吧！你想聊什么话题？"
        else:
            reply_text = "Great! Let's practice English. What topic would you like to discuss?"
        return {
            "success": True,
            "reply": reply_text,
            "lang": "en"
        }

    try:
        # 构建系统提示词
        system_prompt = """你是一位友善的英语学习伙伴。你的任务是帮助用户练习英语对话。

规则：
1. 如果用户说中文：
   - 把中文翻译成自然的英文表达
   - 解释英文表达的用法
   - 鼓励用户用英文回答

2. 如果用户说英文：
   - 回答用户的问题
   - 如果有语法错误，友好地纠正
   - 继续对话，保持话题

3. 回复格式：
   - 用自然的对话方式回复
   - 如果是翻译，同时给出翻译和解释
   - 保持简短（1-3句话）

示例：
用户(中文): "我想问你今天天气怎么样"
AI: "Let me help you ask that! You can say: 'How's the weather today?' or 'What's the weather like today?' Try asking me in English!"

用户(英文): "How's the weather today?"
AI: "It's a beautiful sunny day! Perfect for going for a walk. By the way, did you notice I used 'How's' instead of 'How is'? In casual English, we often contract words like this."
"""
        
        # 构建用户消息
        user_message = f"用户语言: {'中文' if lang == 'zh' else '英文'}\n用户输入: {text}"
        
        # 构建对话历史
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-5:]:  # 只保留最近5条历史
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        messages.append({"role": "user", "content": user_message})
        
        # 调用 LLM
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 200
        }
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"{settings.LLM_BASE_URL}/chat/completions"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            
            # 检测回复语言（简单检测）
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in reply)
            reply_lang = "zh" if has_chinese else "en"
            
            log.debug("AI回复: %s, lang=%s", reply[:50], reply_lang)
            
            return {
                "success": True,
                "reply": reply,
                "lang": reply_lang
            }
            
    except Exception as e:
        log.error("AI对话失败: %s", e)
        return {
            "success": False,
            "error": f"AI对话失败: {str(e)}"
        }


async def synthesize_speech(text: str, lang: str = "en") -> dict[str, Any]:
    """文字转语音。
    
    使用 Edge TTS 进行语音合成（免费）。
    """
    try:
        # Edge TTS 语音名称映射
        voice_map = {
            "zh": "zh-CN-XiaoxiaoNeural",
            "en": "en-US-JennyNeural"
        }
        voice = voice_map.get(lang, "en-US-JennyNeural")
        
        log.debug("TTS请求: text=%s, voice=%s", text[:30], voice)
        
        # 创建临时文件保存音频
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 使用 edge-tts 生成语音
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp_path)
            
            # 读取音频文件并转换为 base64
            with open(tmp_path, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            log.debug("TTS生成成功，音频大小: %d bytes", len(audio_data))
            
            return {
                "success": True,
                "audio": audio_base64
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
    except Exception as e:
        log.error("TTS失败: %s", e)
        return {
            "success": False,
            "error": f"语音合成失败: {str(e)}"
        }
