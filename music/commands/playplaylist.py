# music/commands/playplaylist.py - 提供載入並播放個人播放清單功能的指令 Mixin
import json
import os
import re
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
            配合新的儲存架構，此指令會讀取 `playlists/` 目錄下以 `{user_id}_{playlist_name}.json`
            命名的獨立檔案。佇列中的網址會在播放器迴圈進行串流解析時即時處理。
        """
        if not playlist_name:
            return await ctx.send(
                "請提供要載入並播放的播放清單名稱。\n用法: !playplaylist <名稱>"
            )

        # 延遲初始化：確保 playlists 資料夾存在
        playlists_dir = os.path.join(os.getcwd(), "playlists")
        os.makedirs(playlists_dir, exist_ok=True)

        # 名稱清理，確保能正確對應到儲存時的檔案名稱
        safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "_", playlist_name).strip()
        if not safe_playlist_name:
            return await ctx.send("❌ 播放清單名稱無效。")

        # 取得該使用者的獨立播放清單檔案路徑
        file_path = os.path.join(
            playlists_dir, f"{ctx.author.id}_{safe_playlist_name}.json"
        )

        if not os.path.exists(file_path):
            return await ctx.send(f"❌ 找不到名為「**{playlist_name}**」的播放清單。")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                selected_playlist = json.load(f)
        except Exception as e:
            print(f"PlayPlaylist Error: {e}")
            return await ctx.send("⚠️ 讀取播放清單時發生檔案錯誤。")

        if not selected_playlist or not isinstance(selected_playlist, list):
            return await ctx.send(
                f"播放清單「**{playlist_name}**」中沒有歌曲或檔案損毀。"
            )

        if not ctx.author.voice:
            return await ctx.send("你必須先加入一個語音頻道才能播放音樂。")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        msg = await ctx.send(f"🔄 正在載入播放清單「**{playlist_name}**」...")
        player = get_player(ctx)

        # 將播放清單中的歌曲解析並加入佇列
        for song in selected_playlist:
            song_info = {
                "title": song.get("name", "未知標題"),
                # 這裡存的是 YouTube 永久網址
                "url": song.get("url", ""),
                "webpage_url": song.get("url", ""),
                "duration": song.get("duration", 0),
                "uploader": song.get("uploader", "未知"),
                "thumbnail": song.get("thumbnail"),
            }
            # announce=False 避免一次載入多首歌曲時造成頻道洗版
            await player.add_to_queue(song_info, ctx, announce=False)

        await msg.edit(content=f"🎶 已成功將播放清單「**{playlist_name}**」加入佇列！")
