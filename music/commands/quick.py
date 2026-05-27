# music/commands/quick.py - 提供直接搜尋並播放歌曲功能的指令 Mixin
from typing import Optional
from discord.ext import commands

from music.player import get_player


class QuickCommandMixin:
    """提供快速播放指令的 Mixin 類別。"""

    @commands.command(
        name="quick", aliases=["fast", "play"], help="直接搜尋最相關歌曲並播放"
    )
    async def quick_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        """搜尋 YouTube 上最相關的結果並直接加入佇列播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            query (Optional[str]): 歌曲搜尋關鍵字或直接播放網址。

        Returns:
            None.

        Notes:
            若機器人尚未連接至語音頻道，此指令會自動進行連接。
        """
        if not query:
            return await ctx.send("❌ 請提供歌曲名稱或連結。")

        if not ctx.author.voice:
            return await ctx.send("❌ 你必須先進入語音頻道！")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在為你直接解析並點播：`{query}` ...")

        try:
            # 假設 fetch_song_data 與 extract_info 為 Cog 的成員方法
            data = await self.fetch_song_data(query, 1)
            if not data:
                return await msg.edit(content="❌ 找不到相關歌曲！")

            song_info = self.extract_info(data[0])
            await get_player(ctx).add_to_queue(song_info, ctx)

            await msg.edit(content=f"🎶 已點播「{song_info['title']}」")

        except Exception as e:
            await msg.edit(content=f"⚠️ 點播發生錯誤。錯誤訊息: `{e}`")
