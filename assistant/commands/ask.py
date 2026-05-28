# assistant/commands/ask.py - Gemini 問答指令模組
"""
Discord AI 助理的問答指令模組。

此模組提供了一個 Mixin 類別，封裝了 `/ask` 斜線指令 (Slash Command) 的定義與路由邏輯。
透過將 Discord 的互動事件轉交給底層的服務層 (Services Layer) 處理，實現展示層與
商業邏輯的乾淨分離。
"""

import discord
from discord import app_commands

from assistant.services import ask_gemini
from core.context import InteractionContext


class AskCommandMixin:
    """
    提供 Gemini 問答指令的 Mixin 類別。

    預期被混入 (Mixed-in) 至繼承自 `commands.Cog` 的類別中。
    請注意，繼承此 Mixin 的宿主類別 (Host Class) 必須具備 `ai_service` 屬性
    (實作 IAIService 介面) 才能使此指令正常運作。
    """

    @app_commands.command(name="ask", description="使用 Gemini 問問題並回覆文字")
    @app_commands.describe(question="請輸入要問 Gemini 的問題")
    async def ask_command(
        self, interaction: discord.Interaction, question: str
    ) -> None:
        """
        處理 `/ask` 斜線指令的非同步方法。

        接收使用者輸入的問題，將特定的 Discord `Interaction` 封裝為通用的
        `InteractionContext`，接著將請求與 AI 服務實例一併轉交給 `ask_gemini`
        處理實際的生成與回覆邏輯。

        Args:
            interaction (discord.Interaction): 觸發此指令的 Discord 互動事件物件。
            question (str): 使用者欲詢問 Gemini 的問題內容。
        """
        # 建立通用的互動上下文，並將依賴 (AI 服務) 與參數傳遞給業務邏輯層
        await ask_gemini(InteractionContext(interaction), self.ai_service, question)
