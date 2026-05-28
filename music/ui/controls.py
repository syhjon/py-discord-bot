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

    @discord.ui.button(
        label="⏯️ 播放/暫停",
        style=discord.ButtonStyle.primary,
        custom_id="pause_resume",
    )
    async def pause_resume(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換播放器於暫停與播放狀態之間。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            系統會同步更新播放器的時間計算狀態，確保與語音播放一致。
        """
        vc = self.player.guild.voice_client
        if not vc:
            return await interaction.response.send_message(
                "目前沒有任何歌曲正在播放。", ephemeral=True
            )

        if vc.is_paused():
            vc.resume()
            self.player.resume_time()
            await interaction.response.send_message("▶️ 已繼續播放。", ephemeral=True)
        elif vc.is_playing():
            vc.pause()
            self.player.pause_time()
            await interaction.response.send_message("⏸️ 已暫停播放。", ephemeral=True)

    @discord.ui.button(
        label="⏭️ 跳過", style=discord.ButtonStyle.secondary, custom_id="skip"
    )
    async def skip(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """跳過目前歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            停止播放會喚醒播放器迴圈 (Player Loop) 以載入佇列中的下一首歌曲。
        """
        vc = self.player.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ 已跳過歌曲。", ephemeral=True)
        else:
            await interaction.response.send_message(
                "目前沒有播放任何歌曲可以跳過。", ephemeral=True
            )

    @discord.ui.button(
        label="🔀 隨機播放", style=discord.ButtonStyle.secondary, custom_id="shuffle"
    )
    async def shuffle_queue(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """隨機打亂佇列中的歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            此動作僅影響佇列中的歌曲順序，不會中斷目前正在播放的歌曲。
        """
        if len(self.player.queue) < 2:
            return await interaction.response.send_message(
                "佇列中歌曲太少，無法隨機播放。", ephemeral=True
            )

        random.shuffle(self.player.queue)
        await interaction.response.send_message("🔀 佇列已隨機打亂。", ephemeral=True)

    @discord.ui.button(
        label="⏹️ 停止", style=discord.ButtonStyle.danger, custom_id="stop"
    )
    async def stop(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """停止播放並中斷語音連線。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            此動作會清空佇列並斷開與語音頻道的連線。
        """
        vc = self.player.guild.voice_client
        if vc:
            self.player.queue.clear()
            vc.stop()
            await vc.disconnect()
            await interaction.response.send_message(
                "⏹️ 播放已停止並離開頻道。", ephemeral=True
            )

    @discord.ui.button(
        label="🔄 更新", style=discord.ButtonStyle.success, custom_id="update_progress"
    )
    async def update_progress(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """手動更新播放進度 Embed 資訊。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            此函式會原地編輯現有的 Embed 訊息，而非發送新訊息，以達到資訊同步效果。
        """
        if not self.player.current:
            return await interaction.response.send_message(
                "目前沒有任何歌曲正在播放。", ephemeral=True
            )

        current_time = self.player.get_current_time()
        duration = self.player.current.get("duration", 0)
        progress_bar = create_progress_bar(current_time, duration)
        remaining_time = max(duration - current_time, 0) if duration else 0

        # 取得原訊息中的 Embed 並更新
        embed = interaction.message.embeds[0]
        embed.description = (
            f"⏱️ 時長：{format_time(duration)}\n"
            f"進度：`{progress_bar}`\n"
            f"⏳ 剩餘：{format_time(remaining_time)}"
        )
        await interaction.response.edit_message(embed=embed)
