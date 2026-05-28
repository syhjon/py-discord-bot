# cogs/general.py - Discord 展示層的通用指令 Cog
"""
Discord 機器人的通用指令展示層 (Presentation Layer)。

此模組定義了處理一般性、基礎指令（例如幫助指令）的 Cog 類別，
作為機器人最基本的操作介面之一。
"""

from discord.ext import commands

from general.commands import HelpCommandMixin


class General(HelpCommandMixin, commands.Cog):
    """
    通用指令的 Cog 類別。

    透過繼承 `HelpCommandMixin` 來提供自訂的幫助指令 (Help Command)
    等基礎功能，並作為標準的 `commands.Cog` 掛載至機器人中。
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        初始化 General Cog。

        Args:
            bot (commands.Bot): Discord 機器人實例。
        """
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    """
    Cog 的非同步載入函式 (Setup function)。

    Discord.py 載入擴充模組時會自動呼叫此函式。它負責將初始化後的
    `General` Cog 註冊至機器人中。

    Args:
        bot (commands.Bot): Discord 機器人實例。
    """
    await bot.add_cog(General(bot))
