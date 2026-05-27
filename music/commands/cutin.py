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
            query (Optional[str]): 歌曲搜尋關鍵字或直接播放網址。

        Returns:
            None.

        Notes:
            利用 Player Loop 的機制：先將原歌曲退回佇列前端，
            再將新歌曲放入佇列最前端，最後透過 stop() 觸發換歌，
            避免與底層非同步迴圈發生狀態衝突。
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

            # 插播邏輯：順應 Player Loop 的抓取機制
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if player.current:
                    # 1. 先將原本正在播放的歌塞回佇列最前方 (index 0)
                    player.queue.insert(0, player.current)

                    # 2. 再將這首「插播」的新歌塞到佇列的最前方 (變成新的 index 0, 原歌曲變為 index 1)
                    player.queue.insert(0, song_info)

                    # 3. 停止目前的播放。這會觸發 MusicPlayer 的底層 loop，自動抓取 queue[0] (也就是新歌) 進行播放
                    ctx.voice_client.stop()

                    await msg.edit(
                        content=f"🎶 已將 **{song_info['title']}** 插播並開始播放！原歌曲已排到下一首。"
                    )
            else:
                # 如果目前沒在播歌，就當作一般點歌流程處理
                await player.add_to_queue(song_info, ctx)
                await msg.edit(content=f"🎶 正在播放 \"{song_info['title']}\"。")

        except Exception as e:
            await msg.edit(content=f"⚠️ 插播歌曲時發生錯誤。錯誤訊息: `{e}`")
