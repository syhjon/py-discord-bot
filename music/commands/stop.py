# stop.py - 停止播放音樂（保留佇列與頻道）
from discord.ext import commands

from music.player import players


class StopCommandMixin:
    @commands.command(name="stop", aliases=["停止"], help="停止播放音樂（保留佇列）")
    async def stop_command(self, ctx):
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                # 使用 pause() 停止音訊輸出，能完美保留當前歌曲與後續佇列，且不觸發 player_loop 撥放下一首
                ctx.voice_client.pause()

                # 同步將播放器的計時器暫停，確保進度條不會繼續計算
                if ctx.guild.id in players:
                    players[ctx.guild.id].pause_time()

                await ctx.send("⏹️ 播放已停止，當前歌曲與後續佇列已完整保留。")
            elif ctx.voice_client.is_paused():
                await ctx.send("🎵 音樂目前已經是停止狀態。")
            else:
                await ctx.send("❌ 目前沒有任何歌曲正在播放。")
        else:
            await ctx.send("❌ 機器人目前不在語音頻道中。")
