# music/commands/cutin.py - 提供歌曲優先插入與立即播放功能的指令 Mixin
from typing import Optional
from discord.ext import commands

from music.player import get_player


class CutinCommandMixin:
    """提供插播 (Cut-in) 功能的 Mixin 類別。"""

    @commands.command(
        name="cutin",
        aliases=["insert", "插播", "pn"],
        help="將指定的歌曲插入到播放佇列最前並立即播放",
    )
    async def cutin_command(
        self, ctx: commands.Context, *, query: Optional[str] = None
    ) -> None:
        """將請求的歌曲插入到目前佇列的最前端並立即播放。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            query (str): 歌曲搜尋關鍵字或直接播放網址。

        Returns:
            None.

        Notes:
            若當前有音樂正在播放，該歌曲會被暫停並移動至佇列最前端，
            新插入的歌曲將立刻成為目前的播放項目。
        """
        if not query:
            return await ctx.send("❌ 請提供要插播的歌曲名稱或 URL。")

        if not ctx.author.voice:
            return await ctx.send("❌ 您必須先加入一個語音頻道。")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在處理插播：`{query}` ...")

        try:
            # 假設 fetch_song_data 與 extract_info 為 Cog 的成員方法
            data = await self.fetch_song_data(query, 1)
            if not data:
                return await msg.edit(content="❌ 找不到相關歌曲！")

            song_info = self.extract_info(data[0])
            player = get_player(ctx)

            # 插播邏輯：若有音樂在播放，將現有歌曲放回佇列最前，並替換 current
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if player.current:
                    player.queue.insert(0, player.current)

                player.current = song_info  # 直接替換當前歌曲
                ctx.voice_client.stop()  # 觸發 FFmpeg 切歌流程
                await msg.edit(
                    content=f"🎶 已將 **{song_info['title']}** 插播並開始播放！原歌曲已排到下一首。"
                )
            else:
                await player.add_to_queue(song_info, ctx)
                await msg.edit(content=f"正在播放 \"{song_info['title']}\"。")

        except Exception as e:
            await msg.edit(content=f"⚠️ 插播歌曲時發生錯誤。錯誤訊息: `{e}`")
