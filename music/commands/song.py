# music/commands/song.py - 提供 YouTube 搜尋與互動式選單功能的指令 Mixin
from typing import Optional
import discord
from discord.ext import commands

from music.player import get_player
from music.ui import SongSelect


class SongCommandMixin:
    """提供互動式歌曲搜尋指令的 Mixin 類別。"""

    @commands.command(
        name="song", aliases=["播放"], help="搜尋並透過選單選擇要播放的歌曲"
    )
    async def song_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        """搜尋歌曲並讓使用者從下拉選單中選擇目標項目。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            query (Optional[str]): 歌曲搜尋關鍵字或直接播放網址。

        Returns:
            None.

        Notes:
            若搜尋結果僅有一項（例如直接輸入網址），系統將會自動將該歌曲加入佇列，
            無需額外顯示選單。
        """
        if not query:
            return await ctx.send("❌ 請提供歌曲名稱或連結。")

        if not ctx.author.voice:
            return await ctx.send("❌ 你必須先進入一個語音頻道！")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在搜尋：`{query}` ...")

        try:
            # 假設 fetch_song_data 為 Cog 的成員方法
            top10 = await self.fetch_song_data(query, 10)
            if not top10:
                return await msg.edit(content="❌ 找不到相關歌曲！")

            player = get_player(ctx)

            # 若搜尋結果只有一首（例如直接貼網址），直接加入佇列
            if len(top10) == 1:
                song_info = self.extract_info(top10[0])
                await player.add_to_queue(song_info, ctx)
                return await msg.edit(
                    content=f"🎶 搜尋結果只有一首，已自動點播：「**{song_info['title']}**」"
                )

            # 若結果大於一首，建立互動式選單
            view = discord.ui.View(timeout=60.0)
            view.add_item(SongSelect(top10, player, ctx))
            await msg.edit(content="請從下拉選單中選擇你要播放的歌曲：", view=view)

        except Exception as e:
            await msg.edit(content=f"⚠️ 搜尋歌曲時發生錯誤，請稍後再試！錯誤: `{e}`")
