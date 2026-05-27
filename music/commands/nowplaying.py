# music/commands/nowplaying.py - 提供顯示當前播放歌曲與播放器狀態的指令 Mixin
import discord
from discord.ext import commands

from music.player import get_player
from music.utils import create_progress_bar, format_time


class NowplayingCommandMixin:
    """提供「現在播放 (Now Playing)」功能指令的 Mixin 類別。"""

    @commands.command(
        name="nowplaying", aliases=["np", "now"], help="顯示目前播放的歌曲與播放器狀態"
    )
    async def nowplaying_command(self, ctx: commands.Context) -> None:
        """發送一個包含目前播放狀態資訊的 Embed 訊息。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.

        Notes:
            此 Embed 訊息整合了歌曲進度、原始連結、暫停狀態、音量、循環模式以及佇列長度。
        """
        player = get_player(ctx)

        if not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        # 計算進度條與時長顯示
        current_time = player.get_current_time()
        duration = player.current.get("duration") or 0
        progress_bar = create_progress_bar(current_time, duration)
        duration_display = format_time(duration) if duration > 0 else "未知"

        # 建立 Embed 主體
        embed = discord.Embed(
            title=f"🎶 現在正在播放：**{player.current['title']}**",
            url=player.current.get("webpage_url", ""),
            color=discord.Color.blue(),
        )

        source_url = player.current.get("webpage_url", "未知")
        embed.description = (
            f"`{format_time(current_time)}` {progress_bar} "
            f"`{duration_display}`\n來源：{source_url}"
        )

        # 播放器狀態邏輯處理
        play_state = (
            "⏸️ 暫停中"
            if ctx.voice_client and ctx.voice_client.is_paused()
            else "▶️ 播放中"
        )

        loop_str = "關閉"
        if player.loop_mode == 1:
            loop_str = "🔂 單曲循環"
        elif player.loop_mode == 2:
            loop_str = "🔁 佇列循環"

        status_text = (
            f"**播放狀態：** {play_state}\n"
            f"**播放音量：** 🔊 {int(player.volume * 100)}%\n"
            f"**輪播模式：** {loop_str}\n"
            f"**待播歌曲：** 📜 {len(player.queue)} 首"
        )

        embed.add_field(name="📊 播放器當前狀態", value=status_text, inline=False)

        await ctx.send(embed=embed)
