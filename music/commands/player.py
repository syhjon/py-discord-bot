# music/commands/player.py - 提供私人播放器面板叫出指令
import discord
from discord import app_commands

from core.context import InteractionContext
from music.player import get_existing_player


class PlayerCommandMixin:
    """提供私人播放器介面指令的 Mixin 類別。"""

    @app_commands.command(name="player", description="叫出只有你看得到的播放器介面")
    async def player_command(self, interaction: discord.Interaction) -> None:
        """發送僅呼叫者可見的播放器控制面板。

        Args:
            interaction (discord.Interaction): Discord 斜線指令互動上下文。

        Returns:
            None.

        Notes:
            私人面板不會建立新的音樂播放器；它只操作目前伺服器既有的播放器狀態。
            若播放已結束且播放器已被回收，系統會回覆提示要求使用者重新點歌。
        """
        ctx = InteractionContext(interaction, ephemeral=True)
        player = get_existing_player(ctx)

        if not player or not player.is_active:
            return await ctx.send(
                "目前沒有播放中的播放器，請先使用 `/song` 或 `/quick` 點歌。"
            )

        player.update_context(ctx, search_service=self.youtube_service)
        panel = await player.show_private_panel(ctx, owner_id=interaction.user.id)
        if panel is None:
            await ctx.send("播放器已停止，請重新點歌後再叫出面板。")
