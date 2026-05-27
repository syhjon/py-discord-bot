# music/commands/seek.py - 提供歌曲時間軸跳轉功能的指令 Mixin
from typing import Optional
from discord.ext import commands

from music.player import get_player
from music.utils import format_time


class SeekCommandMixin:
    """提供跳轉 (Seek) 指令的 Mixin 類別。"""

    @commands.command(name="seek", help="跳轉到指定時間 (秒數)")
    async def seek_command(
        self, ctx: commands.Context, seconds: Optional[int] = None
    ) -> None:
        """將當前播放歌曲跳轉至指定的時間點。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            seconds (Optional[int]): 目標跳轉時間（單位：秒，必須為非負數）。

        Returns:
            None.

        Notes:
            系統會透過重新啟動音訊來源並應用 FFmpeg 的 `-ss` 選項來實現跳轉。
            為避免觸發自動切歌邏輯，系統會暫存當前歌曲並強制重新播放。
        """
        if seconds is None or seconds < 0:
            return await ctx.send("請指定要跳轉的有效時間 (秒數)。")

        player = get_player(ctx)

        if (
            not player.current
            or not ctx.voice_client
            or not ctx.voice_client.is_playing()
        ):
            return await ctx.send("目前沒有歌曲正在播放。")

        # 設定跳轉偏移量
        player.seek_offset = seconds

        # 暫存當前歌曲，確保在重新播放時能繼續播放同一首
        current_song = player.current
        player.queue.insert(0, current_song)

        # 觸發停止以觸發 player_loop 的重新載入邏輯
        ctx.voice_client.stop()

        await ctx.send(f"⏩ 已跳轉至 {format_time(seconds)}。")
