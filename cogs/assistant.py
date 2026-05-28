# cogs/assistant.py - Discord 展示層的 AI 助理指令模組
"""
Discord 機器人的 AI 助理指令展示層 (Presentation Layer)。

此模組定義了與 AI 助理（如 Gemini）互動的 Cog 類別，負責處理相關的
Discord 指令輸入，並將請求委派給底層的 AI 服務。
"""

from typing import cast

from discord.ext import commands

from assistant.commands import AskCommandMixin
from core.bot import CustomBot
from domain import IAIService


class Assistant(AskCommandMixin, commands.Cog):
    """
    Gemini 文字助理的 Cog 類別。

    繼承自 `AskCommandMixin` 以提供問答相關的 Discord 指令，
    並作為標準的 `commands.Cog` 掛載至機器人中。
    """

    def __init__(self, bot: commands.Bot, ai_service: IAIService | None = None) -> None:
        """
        初始化 Assistant Cog。

        Args:
            bot (commands.Bot): Discord 機器人實例。
            ai_service (IAIService | None, optional): 注入的 AI 服務實例。
                若未提供，則會自動從自訂機器人的服務容器 (Service Container) 中取得。
                預設為 None。
        """
        self.bot = bot

        # 若未明確提供 AI 服務，則將 bot 轉型為 CustomBot 並從其服務容器中提取
        if ai_service is None:
            ai_service = cast(CustomBot, bot).services.ai

        self.ai_service = ai_service

        # 保留 self.gemini 屬性，供尚未重構或依賴舊名稱的既有 mixin/helper 作為相容性使用。
        self.gemini = ai_service


async def setup(bot: commands.Bot) -> None:
    """
    Cog 的非同步載入函式 (Setup function)。

    Discord.py 載入擴充模組時會自動呼叫此函式。它負責從機器人的服務容器中
    提取並轉型出 AI 服務實例，接著將初始化後的 `Assistant` Cog 註冊至機器人中。

    Args:
        bot (commands.Bot): Discord 機器人實例。
    """
    # 提取服務並確保型別安全
    ai_service = cast(CustomBot, bot).services.ai
    # 將 Cog 加入機器人中
    await bot.add_cog(Assistant(bot, ai_service))
