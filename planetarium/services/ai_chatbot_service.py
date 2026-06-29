"""
AI Chatbot Service
集成大语言模型，提供智能对话能力
"""

import json
import requests
from typing import Dict, List, Optional


class AIChatbotService:
    """AI聊天机器人服务"""

    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url = "https://api.openai.com/v1"
        self._model = "gpt-4o-mini"
        self._conversation_history: List[Dict] = []
        self._system_prompt = "你是一个企业管理系统助手，帮助用户解答业务相关问题。"

    def init(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        """初始化"""
        self._api_key = api_key
        if base_url:
            self._base_url = base_url
        if model:
            self._model = model

    def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        """发送对话消息"""
        if not self._api_key:
            return {"success": False, "message": "AI服务未配置"}

        try:
            messages = [{"role": "system", "content": self._system_prompt}]
            messages.extend(self._conversation_history[-10:])
            messages.append({"role": "user", "content": message})

            response = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"]

                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append({"role": "assistant", "content": reply})

                return {"success": True, "reply": reply}
            else:
                return {"success": False, "message": "AI服务暂时不可用"}

        except Exception as e:
            return {"success": False, "message": f"请求失败: {e}"}

    def clear_history(self):
        """清空对话历史"""
        self._conversation_history.clear()

    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self._system_prompt = prompt

