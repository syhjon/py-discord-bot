import discord

from music.utils import format_time


class SongSelect(discord.ui.Select):
    def __init__(self, top10_results, player, ctx):
        self.top10 = top10_results
        self.player = player
        self.ctx = ctx

        options = []
        for i, video in enumerate(self.top10):
            title = video.get("title", "未知標題")
            if len(title) > 90:
                title = title[:87] + "..."
            duration_str = format_time(video.get("duration", 0))
            uploader = video.get("uploader", "未知")

            options.append(
                discord.SelectOption(
                    label=title,
                    description=f"{uploader} - {duration_str}",
                    value=str(i),
                )
            )

        super().__init__(
            placeholder="請選擇要播放的歌曲...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ 你不能選擇別人搜尋的歌曲喔！", ephemeral=True
            )

        selected_index = int(self.values[0])
        selected_song = self.top10[selected_index]

        song_info = {
            "url": selected_song["url"],
            "webpage_url": selected_song.get("webpage_url", selected_song.get("url")),
            "title": selected_song.get("title", "未知曲目"),
            "duration": selected_song.get("duration", 0),
            "uploader": selected_song.get("uploader", "未知"),
            "thumbnail": (
                selected_song.get("thumbnails", [{"url": ""}])[0]["url"]
                if selected_song.get("thumbnails")
                else None
            ),
        }

        await interaction.response.edit_message(
            content=f"✅ 已選擇歌曲：**{song_info['title']}**", view=None
        )
        await self.player.add_to_queue(song_info, self.ctx)
