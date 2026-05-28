# music/commands/seek.py - 提供歌曲時間軸跳轉功能的指令 Mixin
import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playback_controls import seek_track


class SeekCommandMixin:
    """提供跳轉 (Seek) 指令的 Mixin 類別。"""

    @app_commands.command(name="seek", description="跳轉到指定時間 (秒數)")
    @app_commands.describe(seconds="要跳轉到的秒數")
    async def seek_command(
        self, interaction: discord.Interaction, seconds: int
    ) -> None:
        """將目前播放歌曲跳轉至指定的時間點。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            seconds (Optional[int]): 目標跳轉時間（單位：秒，必須為非負數）。

        Returns:
            None.

        Notes:
            系統會透過重新啟動音訊來源並應用 FFmpeg 的 `-ss` 選項來實現跳轉。
            為避免觸發自動切歌邏輯，系統會暫存目前歌曲並強制重新播放。
        """
        await seek_track(InteractionContext(interaction), seconds)
