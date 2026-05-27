# nowplaying.py - 顯示目前播放的歌曲
import discord
from discord.ext import commands

from music.player import get_player
from music.utils import create_progress_bar, format_time


class NowplayingCommandMixin:
    @commands.command(
        name="nowplaying", aliases=["np", "now"], help="顯示目前播放的歌曲與播放器狀態"
    )
    async def nowplaying_command(self, ctx):
        player = get_player(ctx)
        if not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        current_time = player.get_current_time()
        # 確保 duration 拿不到時為 0，避免報錯
        duration = player.current.get("duration") or 0
        progress_bar = create_progress_bar(current_time, duration)

        # 如果時長是 0 (例如直播)，顯示「未知」而不是「0:00」
        duration_display = format_time(duration) if duration > 0 else "未知"

        embed = discord.Embed(
            title=f"🎶 現在正在播放：**{player.current['title']}**",
            url=player.current.get("webpage_url", ""),
            color=discord.Color.blue(),
        )
        embed.description = f"`{format_time(current_time)}` {progress_bar} `{duration_display}`\n來源：{player.current.get('webpage_url', '未知')}"

        # --- 👇 新增：播放器狀態資訊排版 👇 ---

        # 1. 判斷播放/暫停狀態
        play_state = (
            "⏸️ 暫停中"
            if ctx.voice_client and ctx.voice_client.is_paused()
            else "▶️ 播放中"
        )

        # 2. 判斷循環模式
        loop_str = "關閉"
        if player.loop_mode == 1:
            loop_str = "🔂 單曲循環"
        elif player.loop_mode == 2:
            loop_str = "🔁 佇列循環"

        # 3. 組合狀態文字
        status_text = (
            f"**播放狀態：** {play_state}\n"
            f"**播放音量：** 🔊 {int(player.volume * 100)}%\n"
            f"**輪播模式：** {loop_str}\n"
            f"**待播歌曲：** 📜 {len(player.queue)} 首"
        )

        # 4. 將狀態加入 Embed 的獨立欄位
        embed.add_field(name="📊 播放器當前狀態", value=status_text, inline=False)

        # --- 👆 新增結束 👆 ---

        await ctx.send(embed=embed)
