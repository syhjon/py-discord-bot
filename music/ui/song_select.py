# music/ui/song_select.py - 定義 YouTube 搜尋結果下拉選單
from typing import Any, Dict, List
import discord

from music.context import InteractionContext
from music.utils import format_time


class SongSelect(discord.ui.Select):
    """用於選擇 YouTube 搜尋結果的下拉選單組件。"""

    def __init__(
        self,
        top10_results: List[Dict[str, Any]],
        player: Any,
        ctx: InteractionContext,
    ) -> None:
        """初始化歌曲選擇選單。

        Args:
            top10_results (List[Dict[str, Any]]): 原始的 yt-dlp 搜尋結果字典列表。
            player (Any): 即將接收所選歌曲的 `MusicPlayer` 實例。
            ctx (InteractionContext): 創建選單的斜線指令互動上下文。

        Returns:
            None.

        Notes:
            系統會自動處理標題長度截斷，以符合 Discord UI 元件的顯示限制。
        """
        self.top10: List[Dict[str, Any]] = top10_results
        self.player: Any = player
        self.ctx: InteractionContext = ctx

        options = []
        for i, video in enumerate(self.top10):
            # 處理標題長度，避免超過 Discord 選單上限
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

    async def callback(self, interaction: discord.Interaction) -> None:
        """處理使用者選擇歌曲後的動作。

        Args:
            interaction (discord.Interaction): Discord 下拉選單互動上下文。

        Returns:
            None.

        Notes:
            系統會驗證執行者是否為發起搜尋的使用者，確保操作權限。
        """
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "❌ 你不能選擇別人搜尋的歌曲喔！", ephemeral=True
            )

        selected_index = int(self.values[0])
        selected_song = self.top10[selected_index]

        # 封裝歌曲資訊
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

        # 更新訊息狀態並將歌曲加入佇列
        await interaction.response.edit_message(
            content=f"✅ 已選擇歌曲：**{song_info['title']}**", view=None
        )
        await self.player.add_to_queue(song_info, self.ctx, announce=False)
        await self.ctx.send_public(
            f"✅ {interaction.user.mention} 點播了 **{song_info['title']}**"
        )
