# music/services/gemini.py - 提供 Gemini AI 文字生成整合服務
import os
from typing import Optional
from google import genai
from google.genai import types


class GeminiService:
    """提供 Gemini API 客戶端包裝的服務類別。"""

    def __init__(self) -> None:
        """初始化 Gemini 客戶端。

        Args:
            None.

        Returns:
            None.

        Notes:
            需要設定 `GEMINI_API_KEY` 環境變數。可選設定 `GEMINI_TEXT_MODEL` 來指定模型。
        """
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.text_model: str = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        self.client: Optional[genai.Client] = (
            genai.Client(api_key=self.api_key) if self.api_key else None
        )

    @property
    def is_configured(self) -> bool:
        """檢查 Gemini 服務是否已正確配置。

        Returns:
            bool: 若客戶端已初始化則為 True，反之為 False。
        """
        return bool(self.client)

    async def generate_answer(
        self, question: str, username: Optional[str] = None
    ) -> str:
        """使用 Gemini 生成回應文字。

        Args:
            question (str): 使用者的提問內容。
            username (Optional[str]): 使用者的顯示名稱（選填）。

        Returns:
            str: 生成的回應文字，若無法產生則回傳預設訊息。

        Notes:
            系統會要求 Gemini 以繁體中文回答，並限制內容長度以符合 Discord 的閱讀與顯示需求。
        """
        self._ensure_configured()

        speaker = f"{username} 問：" if username else "使用者問："
        prompt = (
            "你是 Discord 音樂機器人的 AI 助手。\n"
            "請用繁體中文回答，語氣自然、清楚、友善。\n"
            "可以使用簡單 Markdown，但避免表格，盡量控制在 800 字以內。\n\n"
            f"{speaker}{question}"
        )

        # 呼叫 Gemini API 進行內容生成
        response = await self.client.aio.models.generate_content(
            model=self.text_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )

        answer = (response.text or "").strip()
        return answer or "我目前沒有產生可用的回答。"

    def _ensure_configured(self) -> None:
        """確保 Gemini 客戶端已配置，否則拋出執行時期錯誤。

        Raises:
            RuntimeError: 當 API Key 未設定導致客戶端無法建立時拋出。
        """
        if not self.client:
            raise RuntimeError("找不到 GEMINI_API_KEY，請先在 .env 設定。")
