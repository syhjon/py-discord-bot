# music/commands/playplaylist.py - 提供載入並播放個人播放清單功能的指令 Mixin
import json
import os
from typing import Optional
from discord.ext import commands

from music.player import get_player


class PlayPlaylistCommandMixin:
    """提供播放清單載入指令的 Mixin 類別。"""

    @commands.command(
        name="playplaylist", aliases=["ppl"], help="載入並播放您儲存的個人播放清單"
    )
    async def playplaylist_command(
        self, ctx: commands.Context, *, playlist_name: Optional[str] = None
    ) -> None:
        """載入儲存的播放清單並將歌曲加入佇列。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            playlist_name (Optional[str]): 要載入的播放清單名稱。

        Returns:
            None.

        Notes:
            此指令會讀取本地 JSON 檔案中的儲存資訊。佇列中的 YouTube 網址會在
            播放器迴圈 (Player Loop) 進行串流解析時即時處理，確保取得最新資訊。
        """
        if not playlist_name:
            return await ctx.send(
                "請提供要載入並播放的播放清單名稱。\n用法: !playplaylist <名稱>"
            )

        # 取得該使用者的播放清單檔案路徑
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

        # 將播放清單中的歌曲解析並加入佇列
        for song in selected_playlist:
            song_info = {
                "title": song["name"],
                "url": song["url"],  # 這裡存的是 YouTube 永久網址
                "webpage_url": song["url"],
                "duration": song.get("duration") or 0,
                "uploader": song.get("uploader") or "未知",
                "thumbnail": song.get("thumbnail"),
            }
            # announce=False 避免一次載入多首歌曲時造成頻道洗版
            await player.add_to_queue(song_info, ctx, announce=False)

        await msg.edit(content=f"🎶 已成功將播放清單「{playlist_name}」加入佇列！")
