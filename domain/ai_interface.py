# domain/ai_interface.py - AI 服務介面定義模組
"""
AI 服務介面定義模組 (AI service interface definitions)。

此模組定義了應用程式中 AI 服務所必須遵循的抽象協定 (Protocol)。
任何提供 AI 功能的具體實作 (例如 GeminiService 或未來的 OpenAI Service)
皆應滿足此介面定義，從而保證展示層與服務層的高內聚與低耦合。
"""

from typing import Optional, Protocol


class IAIService(Protocol):
    """
    AI 服務的抽象能力介面 (Protocol)。

    作為系統中所有 AI 功能的標準合約 (Contract)，確保注入到 Discord Cogs
    或其他服務中的 AI 實作都具備以下定義的屬性與方法。
    """

    @property
    def is_configured(self) -> bool:
        """
        檢查服務是否已配置完成。

        回傳該 AI 服務是否已經具備呼叫外部 API 的必要設定
        (例如：環境變數中的 API 金鑰是否已成功載入且不為空)。

        Returns:
            bool: 若配置齊全則回傳 True，否則回傳 False。
        """
        ...

    async def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> str:
        """
        根據提供的提示詞 (Prompt) 生成文字內容。

        這是 AI 服務中最核心的方法。呼叫端需提供完整的上下文與問題，
        AI 服務則根據設定的參數回傳生成的文字結果。

        Args:
            prompt (str): 發送給 AI 模型的完整提示詞或問題。
            temperature (float, optional): 控制生成文字的隨機性與創造力。
                數值越高越具隨機性，越低則越保守且確定。預設為 0.3。
            model (Optional[str], optional): 指定要使用的特定模型名稱。
                若為 None，則由具體實作類別決定其預設模型。預設為 None。

        Returns:
            str: AI 模型生成並回傳的純文字結果。
        """
        ...

    async def generate_answer(self, prompt: str, username: Optional[str] = None) -> str:
        """
        [向後相容] 生成問答回覆的輔助方法。

        此方法主要是為了相容舊版架構中已有的呼叫名稱而保留。
        通常具體的實作會在內部將 `prompt` 與 `username` 進行組合後，
        再委由 `generate_text` 來實際執行生成作業。

        Args:
            prompt (str): 發送給 AI 模型的問題或提示詞。
            username (Optional[str], optional): 發問者的名稱，用於提供上下文。
                預設為 None。

        Returns:
            str: AI 模型生成的回覆文字。
        """
        ...
