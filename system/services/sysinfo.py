# system/services/sysinfo.py - 系統與診斷指令的服務模組實作
"""
系統與診斷指令的服務模組 (System and diagnostics service implementation)。

此模組實作了系統層級的資源監控邏輯。透過作業系統介面與 Python 內建的非同步/多執行緒庫，
收集機器人處理程序 (Process) 的 CPU、記憶體使用量，以及當前活躍的執行緒 (Threads)
與非同步任務 (Async Tasks)，並將診斷報告輸出至日誌 (Log) 與 Discord 頻道中。
"""

import asyncio
import logging
import os
import threading

import discord
import psutil

from core.context import InteractionContext

# 取得與主程式同名的 Logger 實例，確保診斷日誌能統一輸出
log = logging.getLogger("MusicBot")


async def send_sysinfo(ctx: InteractionContext) -> None:
    """
    收集並發送系統健康診斷報告。

    此函式會擷取當前 PID 的資源消耗，列舉所有執行緒與非同步任務，
    將詳細資訊記錄於後端終端機，並回傳一份排版整潔的 Embed 給觸發指令的使用者。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    # 先發送提示訊息，因為收集系統狀態(特別是 CPU 計算)可能會有極短暫的延遲
    msg = await ctx.send("📊 正在深入掃描系統資源與背景程序...")

    # 取得目前 Python 執行實例 (Process) 的資源使用狀況
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    # 將 Byte 轉換為 MB (1024 * 1024)
    memory_usage_mb = mem_info.rss / (1024 * 1024)
    # 取得短暫區間內的 CPU 使用率
    cpu_usage = process.cpu_percent(interval=0.1)

    # 收集並格式化所有活躍的執行緒 (Threads)
    threads = threading.enumerate()
    thread_count = len(threads)
    thread_details = []
    for thread in threads:
        # 標註哪一個是主執行緒 (Main Thread)
        is_main = " (Main)" if thread is threading.main_thread() else ""
        thread_details.append(f"• {thread.name}{is_main}")

    thread_str = "\n".join(thread_details)

    # 收集並格式化所有活躍的非同步任務 (Asyncio Tasks)
    task_count = 0
    task_details = []
    try:
        # 取得當前的事件迴圈 (Event Loop) 並獲取所有任務
        loop = asyncio.get_running_loop()
        tasks = asyncio.all_tasks(loop)
        task_count = len(tasks)

        for task in tasks:
            # 嘗試取得協程 (Coroutine) 與任務 (Task) 的名稱，方便除錯追蹤
            coro_name = task.get_coro().__name__ if task.get_coro() else "UnknownCoro"
            task_name = task.get_name()
            task_details.append(f"• [{task_name}] {coro_name}")

        task_str = "\n".join(task_details)
    except RuntimeError:
        # 防呆：若在沒有事件迴圈的環境中執行，避免拋出崩潰例外
        task_str = "無法取得 Asyncio 事件迴圈。"

    # 取得觸發來源資訊供日誌紀錄
    channel_name = getattr(ctx.channel, "name", "未知頻道")
    author_name = getattr(ctx.author, "name", "未知使用者")

    # 寫入後端診斷日誌 (Log)，方便開發者在終端機或伺服器後台查看
    log.info("====== [系統健康診斷報告開始] ======")
    log.info(f"觸發來源頻道: {channel_name} | 觸發者: {author_name}")
    log.info(
        f"PID: {os.getpid()} | CPU: {cpu_usage:.1f}% | RAM: {memory_usage_mb:.2f} MB"
    )
    log.info(f"--- 活躍執行緒清單 (共 {thread_count} 個) ---")
    for thread_name in thread_details:
        log.info(f"  {thread_name}")
    log.info(f"--- 非同步任務清單 (共 {task_count} 個) ---")
    for task_detail in task_details:
        log.info(f"  {task_detail}")
    log.info("====== [系統健康診斷報告結束] ======")

    # Discord Embed 單一欄位 (Field) 有 1024 字元的長度限制。
    # 為了避免超出限制導致發送失敗，此處將字串截斷於 1000 字元。
    if len(thread_str) > 1000:
        thread_str = thread_str[:990] + "\n... (已截斷)"

    if len(task_str) > 1000:
        task_str = task_str[:990] + "\n... (已截斷)"

    # 建構最終要呈現給使用者的 Embed 介面
    embed = discord.Embed(title="⚙️ 機器人系統底層狀態", color=discord.Color.blurple())
    embed.add_field(
        name="🧠 記憶體用量", value=f"**{memory_usage_mb:.2f} MB**", inline=True
    )
    embed.add_field(name="💻 CPU 使用率", value=f"**{cpu_usage:.1f}%**", inline=True)
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

    # 編輯原本的「載入中」訊息，替換為完整的系統報告
    await msg.edit(content=None, embed=embed)
