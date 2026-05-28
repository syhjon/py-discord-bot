# music/commands/sysinfo.py - 提供系統底層資源與程序清單監控功能的指令 Mixin
import asyncio
import logging
import os
import threading

import discord
import psutil
from discord import app_commands

from music.context import InteractionContext

# 取得與 main.py 設定相同的全域 Logger
log = logging.getLogger("MusicBot")


class SysInfoCommandMixin:
    """提供系統資源監控與詳細程序清單的 Mixin 類別。"""

    @app_commands.command(
        name="sysinfo",
        description="查看系統資源與詳細的執行緒/任務清單",
    )
    async def sysinfo_command(self, interaction: discord.Interaction) -> None:
        """收集並顯示目前機器的 CPU、記憶體，以及所有的執行緒和非同步任務清單。

        同時將清單詳細內容輸出至終端機與系統日誌檔中。
        """
        ctx = InteractionContext(interaction)
        msg = await ctx.send("📊 正在深入掃描系統資源與背景程序...")

        # 取得目前 Python 程序的 PID 與硬體消耗
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        memory_usage_mb = mem_info.rss / (1024 * 1024)
        cpu_usage = process.cpu_percent(interval=0.1)

        # ==========================================
        # 收集「系統執行緒 (Threads)」清單
        # ==========================================
        threads = threading.enumerate()
        thread_count = len(threads)
        thread_details = []

        for t in threads:
            is_main = " (Main)" if t is threading.main_thread() else ""
            thread_details.append(f"• {t.name}{is_main}")

        thread_str = "\n".join(thread_details)

        # ==========================================
        # 收集「非同步任務 (Asyncio Tasks)」清單
        # ==========================================
        task_count = 0
        task_details = []
        try:
            loop = asyncio.get_running_loop()
            tasks = asyncio.all_tasks(loop)
            task_count = len(tasks)

            for t in tasks:
                # 萃取任務內部執行的函式名稱 (Coroutine Name)
                coro_name = t.get_coro().__name__ if t.get_coro() else "UnknownCoro"
                task_name = t.get_name()
                task_details.append(f"• [{task_name}] {coro_name}")

            task_str = "\n".join(task_details)
        except RuntimeError:
            task_str = "無法取得 Asyncio 事件迴圈。"

        # ==========================================
        # 寫入終端機與系統日誌 (Log)
        # ==========================================
        log.info("====== [系統健康診斷報告開始] ======")
        log.info(f"觸發來源頻道: {ctx.channel.name} | 觸發者: {ctx.author.name}")
        log.info(
            f"PID: {os.getpid()} | CPU: {cpu_usage:.1f}% | RAM: {memory_usage_mb:.2f} MB"
        )
        log.info(f"--- 活躍執行緒清單 (共 {thread_count} 個) ---")
        for t_name in thread_details:
            log.info(f"  {t_name}")
        log.info(f"--- 非同步任務清單 (共 {task_count} 個) ---")
        for t_detail in task_details:
            log.info(f"  {t_detail}")
        log.info("====== [系統健康診斷報告結束] ======")

        # ==========================================
        # 安全截斷並組裝 Discord Embed 面板
        # ==========================================
        if len(thread_str) > 1000:
            thread_str = thread_str[:990] + "\n... (已截斷)"

        if len(task_str) > 1000:
            task_str = task_str[:990] + "\n... (已截斷)"

        embed = discord.Embed(
            title="⚙️ 機器人系統底層狀態", color=discord.Color.blurple()
        )
        embed.add_field(
            name="🧠 記憶體用量", value=f"**{memory_usage_mb:.2f} MB**", inline=True
        )
        embed.add_field(
            name="💻 CPU 使用率", value=f"**{cpu_usage:.1f}%**", inline=True
        )
        embed.add_field(name="🔢 Process ID", value=f"**{os.getpid()}**", inline=True)

        embed.add_field(
            name=f"🔄 系統執行緒清單 (共 {thread_count} 個)",
            value=f"```text\n{thread_str}\n```",
            inline=False,
        )

        embed.add_field(
            name=f"⚡ 非同步任務清單 (共 {task_count} 個)",
            value=f"```text\n{task_str}\n```",
            inline=False,
        )

        await msg.edit(content=None, embed=embed)
