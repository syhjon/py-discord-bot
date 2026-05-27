# playplaylist.py - 載入並播放個人播放清單
import json
import os

from discord.ext import commands

from music.player import get_player


class PlayPlaylistCommandMixin:
    @commands.command(
        name="playplaylist", aliases=["ppl"], help="載入並播放您儲存的個人播放清單"
    )
    async def playplaylist_command(self, ctx, *, playlist_name: str = None):
        if not playlist_name:
            return await ctx.send(
                "請提供要載入並播放的播放清單名稱。\n用法: !playplaylist <名稱>"
            )
        file_path = os.path.join(self.playlists_dir, f"playlists_{ctx.author.id}.json")

        if not os.path.exists(file_path):
            return await ctx.send("您尚未儲存任何播放清單。")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if playlist_name not in data:
            return await ctx.send(f'找不到名為 "{playlist_name}" 的播放清單。')

        selected_playlist = data[playlist_name]
        if not selected_playlist:
            return await ctx.send(f'播放清單 "{playlist_name}" 中沒有歌曲。')

        if not ctx.author.voice:
            return await ctx.send("你必須先加入一個語音頻道才能播放音樂。")
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔄 正在載入播放清單「{playlist_name}」...")
        player = get_player(ctx)

        # 真正播放前，player.py 的 player_loop 會去即時抓取詳細資料和最新串流！
        for song in selected_playlist:
            song_info = {
                "title": song["name"],
                "url": song["url"],  # 這裡現在存的是 YouTube 永久網址了
                "webpage_url": song["url"],
                "duration": song.get("duration") or 0,
                "uploader": song.get("uploader") or "未知",
                "thumbnail": song.get("thumbnail"),
            }
            # announce=False 避免一次載入 100 首歌洗版頻道
            await player.add_to_queue(song_info, ctx, announce=False)

        await msg.edit(content=f"🎶 已成功將播放清單「{playlist_name}」加入佇列！")
