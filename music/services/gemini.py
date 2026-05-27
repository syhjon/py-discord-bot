import os

from google import genai
from google.genai import types


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    @property
    def is_configured(self):
        return bool(self.client)

    async def generate_answer(self, question, username=None):
        self._ensure_configured()
        speaker = f"{username} 問：" if username else "使用者問："
        prompt = (
            "你是 Discord 音樂機器人的 AI 助手。"
            "請用繁體中文回答，語氣自然、清楚、友善。"
            "可以使用簡單 Markdown，但避免表格，盡量控制在 800 字以內。\n\n"
            f"{speaker}{question}"
        )
        response = await self.client.aio.models.generate_content(
            model=self.text_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )
        answer = (response.text or "").strip()
        return answer or "我目前沒有產生可用的回答。"

    def _ensure_configured(self):
        if not self.client:
            raise RuntimeError("找不到 GEMINI_API_KEY，請先在 .env 設定。")
