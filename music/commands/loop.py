# music/commands/loop.py - 提供播放循環模式設定的指令 Mixin
import discord
from discord import app_commands

from music.context import InteractionContext
from music.player import get_player


class LoopCommandMixin:
    """提供循環模式設定指令的 Mixin 類別。"""

    @app_commands.command(
        name="loop",
        description="設定重播模式",
    )
    @app_commands.describe(mode="off 關閉；song 單曲循環；queue 佇列循環")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="關閉循環", value="off"),
            app_commands.Choice(name="單曲循環", value="song"),
            app_commands.Choice(name="佇列循環", value="queue"),
            app_commands.Choice(name="佇列循環 (all)", value="all"),
        ]
    )
    async def loop_command(
        self, interaction: discord.Interaction, mode: str
    ) -> None:
        """設定播放器的循環模式。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            mode (Optional[str]): 請求的循環模式，可選為 `off`, `song`, `all`, 或 `queue`。

        Returns:
            None.

        Notes:
            循環模式狀態會直接儲存在該伺服器的 `MusicPlayer` 實例中，影響後續的播放流程。
        """
        ctx = InteractionContext(interaction)
        player = get_player(ctx)
        mode = mode.lower() if mode else ""

        if mode == "off":
            player.loop_mode = 0
        elif mode == "song":
            player.loop_mode = 1
        elif mode in ["all", "queue"]:
            player.loop_mode = 2
        else:
            return await ctx.send("請指定循環模式：`off`, `song`, `all`, 或 `queue`。")

        mode_str = (
            "關閉"
            if player.loop_mode == 0
            else "單曲循環" if player.loop_mode == 1 else "佇列循環"
        )
        await ctx.send(f"🔁 循環模式已設定為：{mode_str}。")
