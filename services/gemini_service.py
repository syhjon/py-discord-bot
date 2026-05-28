# services/gemini_service.py - Gemini 文字生成整合服務
"""
此模組負責封裝 Google Gemini API 的用戶端實例與呼叫邏輯。
提供非同步的方法以生成文字回應，呼叫端可依自己的功能情境傳入 prompt。
"""

import os
from typing import Any, Optional


class GeminiService:
    """通用的 Gemini API 客戶端包裝類別。"""

    def __init__(self) -> None:
        """初始化 Gemini 服務實例。

        將從環境變數中讀取 API 金鑰 (GEMINI_API_KEY) 與使用的文字模型名稱 (GEMINI_TEXT_MODEL)。
        若有提供有效的 API 金鑰，則建立對應的 genai.Client 實例。
        """
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.text_model: str = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        self.client: Optional[Any] = None
        self._types: Optional[Any] = None
        self._import_error: Optional[Exception] = None

        if self.api_key:
            try:
                from google import genai
                from google.genai import types
            except Exception as e:
                self._import_error = e
            else:
                self._types = types
                self.client = genai.Client(api_key=self.api_key)

    @property
    def is_configured(self) -> bool:
        """檢查 Gemini 服務是否已成功配置。"""
        return bool(self.client)

    async def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> str:
        """使用呼叫端提供的 prompt 生成文字回覆。"""
        client = self._get_client()

        response = await client.aio.models.generate_content(
            model=model or self.text_model,
            contents=prompt,
            config=self._types.GenerateContentConfig(temperature=temperature),
        )

        answer = (response.text or "").strip()
        return answer or "我目前沒有產生可用的回答。"

    async def generate_answer(
        self, prompt: str, username: Optional[str] = None
    ) -> str:
        """相容舊呼叫名稱的文字生成方法。

        新功能應優先使用 `generate_text()`。此方法會把第一個參數視為完整
        prompt，不再附加任何特定功能的角色提示詞；`username` 僅保留舊簽名相容。
        """
        return await self.generate_text(prompt)

    def _get_client(self) -> Any:
        """取得已配置完成的 Gemini API 客戶端。"""
        if self._import_error:
            raise RuntimeError("找不到 google-genai 套件，請先安裝 Gemini SDK。")
        if not self.client:
            raise RuntimeError("找不到 GEMINI_API_KEY，請先在 .env 設定。")
        return self.client
