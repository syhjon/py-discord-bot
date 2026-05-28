# music/commands/help.py - 提供分頁式指令教學與說明功能的指令 Mixin
from typing import Optional
import discord
from discord import app_commands

from music.context import InteractionContext
from music.ui import HelpPagination


class HelpCommandMixin:
    """提供自訂教學指令的 Mixin 類別。"""

    @app_commands.command(name="help", description="顯示所有可用的斜線指令")
    @app_commands.describe(specific_cmd="要查看詳細說明的指令名稱")
    async def help_command(
        self, interaction: discord.Interaction, specific_cmd: Optional[str] = None
    ) -> None:
        """顯示特定指令說明或分頁式的完整指令列表。

        Args:
            interaction (discord.Interaction): Discord 斜線指令互動上下文。
            specific_cmd (Optional[str]): 選填，指定要查詢的指令名稱。

        Returns:
            None.

        Notes:
            由於 `main.py` 已停用內建的 discord.py help 指令，此自訂指令將負責處理所有面向使用者的教學輸出。
        """
        ctx = InteractionContext(interaction)
        all_commands = sorted(self.bot.tree.get_commands(), key=lambda c: c.name)

        # 處理單一指令詳細說明查詢
        if specific_cmd:
            cmd = discord.utils.get(all_commands, name=specific_cmd.lower())

            if not cmd:
                return await ctx.send(f'沒有找到名為 "{specific_cmd}" 的指令。')

            usage_params = []
            for param in getattr(cmd, "parameters", []):
                if param.required:
                    usage_params.append(f"<{param.name}>")
                else:
                    usage_params.append(f"[{param.name}]")
            usage = " ".join([f"/{cmd.name}", *usage_params])

            embed = discord.Embed(
                title=f"指令：/{cmd.name}",
                description=cmd.description or "無",
                color=discord.Color.blue(),
            )
            embed.add_field(name="用法", value=usage)
            return await ctx.send(embed=embed)

        # 處理完整指令分頁列表
        commands_per_page = 10
        embeds = []
        for i in range(0, len(all_commands), commands_per_page):
            page_cmds = all_commands[i : i + commands_per_page]
            embed = discord.Embed(
                title="可用指令列表",
                description=f"總共有 {len(all_commands)} 個指令。",
                color=discord.Color.blue(),
            )

            for cmd in page_cmds:
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description or "無描述",
                    inline=False,
                )

            total_pages = (len(all_commands) - 1) // commands_per_page + 1
            current_page_num = i // commands_per_page + 1
            embed.set_footer(
                text=f"頁數 {current_page_num}/{total_pages} | 使用 /help <指令名稱> 查看詳細資訊。"
            )
            embeds.append(embed)

        # 發送嵌入訊息 (若只有一頁則直接發送，超過則使用翻頁元件)
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            await ctx.send(embed=embeds[0], view=HelpPagination(embeds))
