# general/services/help.py - 處理幫助指令的服務層模組
"""
機器人幫助指令的服務邏輯層 (Services Layer)。

此模組負責處理 `/help` 指令的核心商業邏輯。它會動態從機器人的 CommandTree
中提取已註冊的斜線指令 (Slash Commands)，並根據使用者的請求，生成特定指令
的詳細說明 Embed，或是所有指令的分頁列表介面。
"""

from typing import Optional

import discord

from core.context import InteractionContext
from general.ui import HelpPagination


async def send_help(
    ctx: InteractionContext, bot: discord.Client, specific_cmd: Optional[str] = None
) -> None:
    """
    產生並發送機器人的指令幫助說明。

    根據是否提供特定指令名稱，此函式會呈現兩種不同的行為：
    1. 若提供 `specific_cmd`：搜尋該指令並回傳包含參數用法的詳細說明。
    2. 若未提供：回傳所有可用指令的列表，若超過 10 個指令則自動加入分頁按鈕 UI。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        bot (discord.Client): Discord 機器人實例，用於提取 CommandTree 中的指令資料。
        specific_cmd (Optional[str], optional): 使用者指定查詢的特定指令名稱。預設為 None。
    """
    # 取得機器人註冊的所有斜線指令，並依指令名稱進行字母順序排列
    all_commands = sorted(bot.tree.get_commands(), key=lambda c: c.name)

    # 模式一：查詢單一特定指令的詳細說明
    if specific_cmd:
        # 將輸入轉為小寫並在指令列表中搜尋
        cmd = discord.utils.get(all_commands, name=specific_cmd.lower())
        if not cmd:
            return await ctx.send(f'沒有找到名為 "{specific_cmd}" 的指令。')

        # 組合指令的使用方法 (Usage)
        usage_params = []
        for param in getattr(cmd, "parameters", []):
            if param.required:
                # 必填參數使用 < > 包覆
                usage_params.append(f"<{param.name}>")
            else:
                # 選填參數使用 [ ] 包覆
                usage_params.append(f"[{param.name}]")

        usage = " ".join([f"/{cmd.name}", *usage_params])

        # 建構詳細說明的 Embed
        embed = discord.Embed(
            title=f"指令：/{cmd.name}",
            description=cmd.description or "無",
            color=discord.Color.blue(),
        )
        embed.add_field(name="用法", value=usage)

        return await ctx.send(embed=embed)

    # 模式二：顯示所有可用指令的列表 (支援分頁)
    commands_per_page = 10
    embeds = []

    # 將所有指令依指定的每頁數量進行切割
    for i in range(0, len(all_commands), commands_per_page):
        page_cmds = all_commands[i : i + commands_per_page]

        embed = discord.Embed(
            title="可用指令列表",
            description=f"總共有 {len(all_commands)} 個指令。",
            color=discord.Color.blue(),
        )

        # 將當前頁面的指令逐一加入 Embed 欄位中
        for cmd in page_cmds:
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "無描述",
                inline=False,
            )

        # 計算總頁數與當前頁數，並顯示在底部 (Footer)
        total_pages = (len(all_commands) - 1) // commands_per_page + 1
        current_page_num = i // commands_per_page + 1
        embed.set_footer(
            text=f"頁數 {current_page_num}/{total_pages} | 使用 /help <指令名稱> 查看詳細資訊。"
        )
        embeds.append(embed)

    # 根據產生出來的頁數決定是否需要附加分頁 UI (View)
    if len(embeds) == 1:
        # 若只有一頁，直接發送 Embed
        await ctx.send(embed=embeds[0])
    else:
        # 若有多頁，附上 HelpPagination 視圖以提供上一頁/下一頁按鈕
        await ctx.send(embed=embeds[0], view=HelpPagination(embeds))
