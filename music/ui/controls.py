import random

import discord

from music.utils import create_progress_bar, format_time


class PlayerControls(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    @discord.ui.button(
        label="⏯️ 播放/暫停",
        style=discord.ButtonStyle.primary,
        custom_id="pause_resume",
    )
    async def pause_resume(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
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
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    ):
        if len(self.player.queue) < 2:
            return await interaction.response.send_message(
                "佇列中歌曲太少，無法隨機播放。", ephemeral=True
            )
        random.shuffle(self.player.queue)
        await interaction.response.send_message("🔀 佇列已隨機打亂。", ephemeral=True)

    @discord.ui.button(
        label="⏹️ 停止", style=discord.ButtonStyle.danger, custom_id="stop"
    )
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    ):
        if not self.player.current:
            return await interaction.response.send_message(
                "目前沒有任何歌曲正在播放。", ephemeral=True
            )
        current_time = self.player.get_current_time()
        duration = self.player.current.get("duration", 0)
        progress_bar = create_progress_bar(current_time, duration)
        remaining_time = max(duration - current_time, 0) if duration else 0
        embed = interaction.message.embeds[0]
        embed.description = f"⏱️ 時長：{format_time(duration)}\nProgress: `{progress_bar}`\n⏳ 剩餘：{format_time(remaining_time)}"
        await interaction.response.edit_message(embed=embed)
