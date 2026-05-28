# cogs/system.py - Discord 展示層的系統診斷 Cog
"""
Discord 機器人的系統診斷指令展示層 (Presentation Layer)。

此模組定義了處理系統資訊與診斷相關指令的 Cog 類別，
方便開發者或管理員查看機器人目前的運行環境與資源狀態。
"""

from discord.ext import commands

from system.commands import SysInfoCommandMixin


class System(SysInfoCommandMixin, commands.Cog):
    """
    系統診斷的 Cog 類別。

    透過繼承 `SysInfoCommandMixin` 來提供系統資訊查詢指令
    (例如 CPU、記憶體使用率、伺服器狀態等)，並作為標準的
    `commands.Cog` 掛載至機器人中。
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        初始化 System Cog。

        Args:
            bot (commands.Bot): Discord 機器人實例。
        """
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    """
    Cog 的非同步載入函式 (Setup function)。

    Discord.py 載入擴充模組時會自動呼叫此函式。它負責將初始化後的
    `System` Cog 註冊至機器人中。

    Args:
        bot (commands.Bot): Discord 機器人實例。
    """
    await bot.add_cog(System(bot))
