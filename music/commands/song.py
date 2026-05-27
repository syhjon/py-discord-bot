# song.py - 搜尋並選擇歌曲的指令
import discord
from discord.ext import commands

from music.player import get_player
from music.ui import SongSelect


class SongCommandMixin:
    @commands.command(
        name="song", aliases=["播放"], help="搜尋並透過選單選擇要播放的歌曲"
    )
    async def song_command(self, ctx, *, query: str = None):
        if not query:
            return await ctx.send("❌ 請提供歌曲名稱或連結。")
        if not ctx.author.voice:
            return await ctx.send("❌ 你必須先進入一個語音頻道！")
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在搜尋：`{query}` ...")
        try:
            top10 = await self.fetch_song_data(query, 10)
            if not top10:
                return await msg.edit(content="❌ 找不到相關歌曲！")

            player = get_player(ctx)

            # 新增邏輯：如果搜尋結果只有一首（例如直接貼網址），就自動加入佇列
            if len(top10) == 1:
                song_info = self.extract_info(top10[0])
                await player.add_to_queue(song_info, ctx)
                return await msg.edit(
                    content=f"🎶 搜尋結果只有一首，已自動點播：「**{song_info['title']}**」"
                )

            # 若結果大於一首，則維持原來的下拉選單邏輯
            view = discord.ui.View(timeout=60.0)
            view.add_item(SongSelect(top10, player, ctx))
            await msg.edit(content="請從下拉選單中選擇你要播放的歌曲：", view=view)

        except Exception as e:
            await msg.edit(content=f"⚠️ 搜尋歌曲時發生錯誤，請稍後再試！錯誤: `{e}`")
