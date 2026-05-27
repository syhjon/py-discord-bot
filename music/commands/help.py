# music/commands/help.py - 提供分頁式指令教學與說明功能的指令 Mixin
from typing import Optional
import discord
from discord.ext import commands

from music.ui import HelpPagination


class HelpCommandMixin:
    """提供自訂教學指令的 Mixin 類別。"""

    @commands.command(
        name="help",
        aliases=["commands", "h", "指令", "教學"],
        help="顯示所有可用的指令（分頁顯示）",
    )
    async def help_command(
        self, ctx: commands.Context, specific_cmd: Optional[str] = None
    ) -> None:
        """顯示特定指令說明或分頁式的完整指令列表。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            specific_cmd (Optional[str]): 選填，指定要查詢的指令名稱或別名。

        Returns:
            None.

        Notes:
            由於 `main.py` 已停用內建的 discord.py help 指令，此自訂指令將負責處理所有面向使用者的教學輸出。
        """
        all_commands = [c for c in self.bot.commands if not c.hidden]

        # 處理單一指令詳細說明查詢
        if specific_cmd:
            cmd = discord.utils.get(
                all_commands, name=specific_cmd.lower()
            ) or discord.utils.get(all_commands, aliases=[specific_cmd.lower()])

            if not cmd:
                return await ctx.send(f'沒有找到名為 "{specific_cmd}" 的指令。')

            embed = discord.Embed(
                title=f"指令：{cmd.name}",
                description=cmd.help or "無",
                color=discord.Color.blue(),
            )
            aliases_str = (
                f"`!{'`, `!'.join(cmd.aliases)}`" if cmd.aliases else "沒有別名。"
            )
            embed.add_field(name="用法", value=f"!{cmd.name}")
            embed.add_field(name="別名", value=aliases_str)
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
                aliases_str = (
                    f" (別名: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                )
                embed.add_field(
                    name=f"!{cmd.name}{aliases_str}",
                    value=cmd.help or "無描述",
                    inline=False,
                )

            total_pages = (len(all_commands) - 1) // commands_per_page + 1
            current_page_num = i // commands_per_page + 1
            embed.set_footer(
                text=f"頁數 {current_page_num}/{total_pages} | 使用 !help <指令名稱> 查看詳細資訊。"
            )
            embeds.append(embed)

        # 發送嵌入訊息 (若只有一頁則直接發送，超過則使用翻頁元件)
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            await ctx.send(embed=embeds[0], view=HelpPagination(embeds))
