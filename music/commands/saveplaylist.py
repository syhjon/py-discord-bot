# saveplaylist.py - 儲存目前的播放佇列為個人播放清單
import json
import os

from discord.ext import commands

from music.player import get_player


class SavePlaylistCommandMixin:
    @commands.command(
        name="saveplaylist", aliases=["sl"], help="將目前的播放佇列儲存為個人播放清單"
    )
    async def saveplaylist_command(self, ctx, *, playlist_name: str = None):
        if not playlist_name:
            return await ctx.send(
                "請提供播放清單名稱。\n用法: !saveplaylist <播放清單名稱>"
            )
        player = get_player(ctx)
        if not player.queue and not player.current:
            return await ctx.send("目前播放佇列中沒有歌曲，無法儲存。")

        file_path = os.path.join(self.playlists_dir, f"playlists_{ctx.author.id}.json")
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # 包含目前正在播放的歌加上佇列的歌
        save_list = []
        if player.current:
            save_list.append(
                {
                    "name": player.current["title"],
                    # 優先抓取永久網址，如果沒有才退回 url
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

        data[playlist_name] = save_list
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await ctx.send(f"✅ 已將目前的佇列儲存為播放清單：{playlist_name}")
