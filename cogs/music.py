# cogs/music.py - 音樂播放的主要 Cog，負責註冊指令和管理播放器
from discord.ext import commands
from music.cog import Music


async def setup(bot: commands.Bot) -> None:
    """將 Music Cog 註冊至 Discord 機器人。

    Args:
        bot (commands.Bot): 目前正在運作中的 Discord 機器人實例。

    Returns:
        None.

    Notes:
        這是 `discord.py` 擴充功能 (Extension) 的標準進入點函式。
        系統在載入此模組時會自動呼叫此函式以進行 Cog 註冊。
    """
    await bot.add_cog(Music(bot))