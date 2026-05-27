# quick.py - 直接搜尋並播放最相關的歌曲
from discord.ext import commands

from music.player import get_player


class QuickCommandMixin:
    @commands.command(
        name="quick", aliases=["fast", "play"], help="直接搜尋最相關歌曲並播放"
    )
    async def quick_command(self, ctx, *, query: str = None):
        if not query:
            return await ctx.send("❌ 請提供歌曲名稱或連結。")
        if not ctx.author.voice:
            return await ctx.send("❌ 你必須先進入語音頻道！")
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在為你直接解析並點播：`{query}` ...")
        try:
            data = await self.fetch_song_data(query, 1)
            if not data:
                return await msg.edit(content="❌ 找不到相關歌曲！")
            song_info = self.extract_info(data[0])
            await get_player(ctx).add_to_queue(song_info, ctx)
            await msg.edit(content=f"🎶 已點播「{song_info['title']}」")
        except Exception as e:
            await msg.edit(content=f"⚠️ 點播發生錯誤。錯誤訊息: `{e}`")
