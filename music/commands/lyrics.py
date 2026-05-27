import urllib.parse

import aiohttp
from discord.ext import commands

from music.player import get_player


class LyricsCommandMixin:
    @commands.command(name="lyrics", aliases=["ly"], help="搜尋目前播放歌曲的歌詞")
    async def lyrics_command(self, ctx):
        player = get_player(ctx)
        if not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")
        title = player.current["title"]
        msg = await ctx.send(f"🔍 正在搜尋 **{title}** 的歌詞...")

        try:
            # 這裡借用一個免費的歌詞 API 來取代 lyrics-finder
            url = (
                f"https://some-random-api.com/lyrics?title={urllib.parse.quote(title)}"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        lyrics = data.get("lyrics", "")
                        if lyrics:
                            if len(lyrics) > 2000:
                                lyrics = lyrics[:1997] + "..."
                            return await msg.edit(
                                content=f"**{title} 的歌詞：**\n{lyrics}"
                            )
            await msg.edit(content="❌ 找不到這首歌的歌詞。")
        except:
            await msg.edit(content="⚠️ 搜尋歌詞時發生錯誤。")
