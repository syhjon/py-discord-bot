# music/commands/saveplaylist.py - 提供儲存目前播放狀態為播放清單功能的指令 Mixin
import json
import os
from typing import Optional
from discord.ext import commands

from music.player import get_player


class SavePlaylistCommandMixin:
    """提供儲存播放清單指令的 Mixin 類別。"""

    @commands.command(
        name="saveplaylist", aliases=["sl"], help="將目前的播放佇列儲存為個人播放清單"
    )
    async def saveplaylist_command(
        self, ctx: commands.Context, *, playlist_name: Optional[str] = None
    ) -> None:
        """將目前的播放狀態（包含當前歌曲與佇列）儲存為使用者命名的播放清單。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            playlist_name (Optional[str]): 欲儲存的播放清單名稱。

        Returns:
            None.

        Notes:
            播放清單會以 JSON 格式儲存在專案目錄下的 `playlists` 資料夾中，並以 Discord
            使用者 ID 分隔，確保各使用者的資料獨立性。
        """
        if not playlist_name:
            return await ctx.send(
                "請提供播放清單名稱。\n用法: !saveplaylist <播放清單名稱>"
            )

        player = get_player(ctx)
        if not player.queue and not player.current:
            return await ctx.send("目前播放佇列中沒有歌曲，無法儲存。")

        # 讀取現有儲存資料
        file_path = os.path.join(self.playlists_dir, f"playlists_{ctx.author.id}.json")
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # 收集當前播放歌曲與佇列中的歌曲
        save_list = []
        if player.current:
            save_list.append(
                {
                    "name": player.current["title"],
                    # 優先使用永久網址，若無則退回使用 url
                    "url": player.current.get("webpage_url", player.current["url"]),
                    "duration": player.current.get("duration") or 0,
                    "uploader": player.current.get("uploader") or "未知",
                    "thumbnail": player.current.get("thumbnail"),
                }
            )

        for song in player.queue:
            save_list.append(
                {
                    "name": song["title"],
                    "url": song.get("webpage_url", song["url"]),
                    "duration": song.get("duration") or 0,
                    "uploader": song.get("uploader") or "未知",
                    "thumbnail": song.get("thumbnail"),
                }
            )

        # 更新並寫入檔案
        data[playlist_name] = save_list
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await ctx.send(f"✅ 已將目前的佇列儲存為播放清單：{playlist_name}")
