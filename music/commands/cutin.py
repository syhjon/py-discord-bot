from discord.ext import commands

from music.player import get_player


class CutinCommandMixin:
    @commands.command(
        name="cutin",
        aliases=["insert", "插播", "pn"],
        help="將指定的歌曲插入到播放佇列最前並立即播放",
    )
    async def cutin_command(self, ctx, *, query: str = None):
        if not query:
            return await ctx.send("❌ 請提供要插播的歌曲名稱或 URL。")
        if not ctx.author.voice:
            return await ctx.send("❌ 您必須先加入一個語音頻道。")
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔍 正在處理插播：`{query}` ...")
        try:
            data = await self.fetch_song_data(query, 1)
            if not data:
                return await msg.edit(content="❌ 找不到相關歌曲！")
            song_info = self.extract_info(data[0])
            player = get_player(ctx)

            # 插播邏輯：如果有歌在播，把正在播的放回佇列最前，把插播的放第一位，然後切歌
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if player.current:
                    player.queue.insert(0, player.current)
                player.current = song_info  # 直接換掉 current
                ctx.voice_client.stop()  # 觸發切歌
                await msg.edit(
                    content=f"🎶 已將 **{song_info['title']}** 插播並開始播放！原歌曲已排到下一首。"
                )
            else:
                await player.add_to_queue(song_info, ctx)
                await msg.edit(content=f"正在播放 \"{song_info['title']}\"。")
        except Exception as e:
            await msg.edit(content=f"⚠️ 插播歌曲時發生錯誤。錯誤訊息: `{e}`")
