# music/ui/controls.py - 定義持久化的播放控制按鈕介面
import random
from typing import Any

import discord

from music.utils import create_progress_bar, format_time


class PlayerControls(discord.ui.View):
    """用於目前播放歌曲的互動式控制按鈕視圖。"""

    def __init__(self, player: Any) -> None:
        """初始化播放器控制介面。

        Args:
            player (Any): 該視圖所控制的 `MusicPlayer` 實例。

        Returns:
            None.

        Notes:
            設定 `timeout=None` 以確保只要訊息存在，控制按鈕就會持續保持作用。
        """
        super().__init__(timeout=None)
        self.player = player

    async def _update_panel_status(
        self, interaction: discord.Interaction, status_msg: str
    ) -> None:
        """共用輔助方法：原地更新面板的進度條，並在最底下的頁尾顯示操作狀態。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            status_msg (str): 要顯示在面板最底下的狀態提示文字。
        """
        # 防呆：如果找不到原本的 Embed，就退回原本的發送提示方式
        if not interaction.message or not interaction.message.embeds:
            return await interaction.response.send_message(status_msg, ephemeral=True)

        embed = interaction.message.embeds[0]

        # 將狀態訊息寫入面板最底下 (Footer)
        embed.set_footer(text=f"操作狀態：{status_msg}")

        # 同步更新面板上的播放進度
        if self.player.current:
            current_time = self.player.get_current_time()
            duration = self.player.current.get("duration", 0)
            progress_bar = create_progress_bar(current_time, duration)
            remaining_time = max(duration - current_time, 0) if duration else 0

            embed.description = (
                f"⏱️ 時長：{format_time(duration)}\n"
                f"進度：`{progress_bar}`\n"
                f"⏳ 剩餘：{format_time(remaining_time)}"
            )

        # 原地編輯訊息，不會發出新對話
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(
        label="⏯️ 播放/暫停",
        style=discord.ButtonStyle.primary,
        custom_id="pause_resume",
    )
    async def pause_resume(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換播放器於暫停與播放狀態之間。"""
        vc = self.player.guild.voice_client
        if not vc:
            return await self._update_panel_status(
                interaction, "❌ 目前沒有任何歌曲正在播放。"
            )

        if vc.is_paused():
            vc.resume()
            self.player.resume_time()
            await self._update_panel_status(interaction, "▶️ 已繼續播放。")
        elif vc.is_playing():
            vc.pause()
            self.player.pause_time()
            await self._update_panel_status(interaction, "⏸️ 已暫停播放。")

    @discord.ui.button(
        label="⏭️ 跳過", style=discord.ButtonStyle.secondary, custom_id="skip"
    )
    async def skip(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """跳過目前歌曲。"""
        vc = self.player.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await self._update_panel_status(
                interaction, "⏭️ 已跳過歌曲，準備播放下一首。"
            )
        else:
            await self._update_panel_status(
                interaction, "⚠️ 目前沒有播放任何歌曲可以跳過。"
            )

    @discord.ui.button(
        label="🔀 隨機播放", style=discord.ButtonStyle.secondary, custom_id="shuffle"
    )
    async def shuffle_queue(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """隨機打亂佇列中的歌曲。"""
        if len(self.player.queue) < 2:
            return await self._update_panel_status(
                interaction, "⚠️ 佇列中歌曲太少，無法隨機播放。"
            )

        random.shuffle(self.player.queue)
        await self._update_panel_status(interaction, "🔀 佇列已隨機打亂。")

    @discord.ui.button(
        label="⏹️ 停止", style=discord.ButtonStyle.danger, custom_id="stop"
    )
    async def stop(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """停止播放（暫停音樂並保留佇列與連線）。"""
        vc = self.player.guild.voice_client
        if vc:
            if vc.is_playing():
                vc.pause()
                self.player.pause_time()

            await self._update_panel_status(
                interaction, "⏹️ 已暫停，保留佇列與連線 (按「⏯️ 播放」繼續)"
            )
        else:
            await self._update_panel_status(interaction, "⚠️ 目前沒有連接語音頻道。")

    @discord.ui.button(
        label="🔄 更新", style=discord.ButtonStyle.success, custom_id="update_progress"
    )
    async def update_progress(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """手動更新播放進度 Embed 資訊。"""
        if not self.player.current:
            return await self._update_panel_status(
                interaction, "❌ 目前沒有任何歌曲正在播放。"
            )

        # 這裡直接呼叫共用方法，並提示已更新
        await self._update_panel_status(interaction, "🔄 面板進度已同步。")
