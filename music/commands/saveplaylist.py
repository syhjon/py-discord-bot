# music/commands/saveplaylist.py - 提供儲存目前播放狀態為播放清單功能的指令 Mixin
import json
import os
import re
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class SavePlaylistCommandMixin:
    """提供儲存播放清單指令的 Mixin 類別。"""

    @app_commands.command(
        name="saveplaylist", description="將目前的播放佇列儲存為個人播放清單"
    )
    @app_commands.describe(playlist_name="播放清單名稱")
    async def saveplaylist_command(
        self, interaction: discord.Interaction, playlist_name: str
    ) -> None:
        """將目前的播放狀態（包含目前歌曲與佇列）儲存為單一獨立的播放清單檔案。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            playlist_name (Optional[str]): 欲儲存的播放清單名稱。

        Returns:
            None.

        Notes:
            檔案將會儲存在 `storage/playlists/` 目錄下，命名格式為 `{user_id}_{playlist_name}.json`，
            以此確保每位使用者的播放清單獨立且不會互相覆蓋。
        """
        ctx = InteractionContext(interaction)
        if not playlist_name:
            return await ctx.send(
                "請提供播放清單名稱。\n用法: /saveplaylist <播放清單名稱>"
            )

        player = get_player(ctx)
        if not player.queue and not player.current:
            return await ctx.send("目前播放佇列中沒有歌曲，無法儲存。")

        # 延遲初始化：確保 playlists 資料夾存在，避免 AttributeError
        playlists_dir = os.path.join(os.getcwd(), "storage", "playlists")
        os.makedirs(playlists_dir, exist_ok=True)

        # 檔案名稱清理：過濾掉作業系統不允許的非法路徑字元，防止路徑穿越 (Path Traversal) 或寫入錯誤
        safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "_", playlist_name).strip()
        if not safe_playlist_name:
            return await ctx.send("❌ 播放清單名稱包含過多無效字元，請更換一個名稱。")

        # 建構獨立的檔案路徑，例如：00000_boo.json
        file_path = os.path.join(
            playlists_dir, f"{ctx.author.id}_{safe_playlist_name}.json"
        )

        # 收集目前播放歌曲與佇列中的歌曲
        save_list = []
        if player.current:
            save_list.append(
                {
                    "name": player.current.get("title", "未知標題"),
                    # 優先使用永久網址 (webpage_url)，若無則退回使用 url
                    "url": player.current.get("webpage_url", player.current.get("url")),
                    "duration": player.current.get("duration", 0),
                    "uploader": player.current.get("uploader", "未知"),
                    "thumbnail": player.current.get("thumbnail"),
                }
            )

        for song in player.queue:
            save_list.append(
                {
                    "name": song.get("title", "未知標題"),
                    "url": song.get("webpage_url", song.get("url")),
                    "duration": song.get("duration", 0),
                    "uploader": song.get("uploader", "未知"),
                    "thumbnail": song.get("thumbnail"),
                }
            )

        # 直接將陣列寫入使用者的專屬播放清單檔案
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_list, f, ensure_ascii=False, indent=2)
            await ctx.send(f"✅ 已將目前的佇列儲存為播放清單：**{playlist_name}**")
        except Exception as e:
            print(f"SavePlaylist Error: {e}")
            await ctx.send("⚠️ 儲存播放清單時發生系統錯誤，請稍後再試。")
