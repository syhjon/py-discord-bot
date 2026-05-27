from discord.ext import commands

from music.player import get_player


class LoopCommandMixin:
    @commands.command(
        name="loop",
        aliases=["repeat", "replay"],
        help="重播模式。off：關閉循環；song：單曲循環；queue：佇列循環",
    )
    async def loop_command(self, ctx, mode: str = None):
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
