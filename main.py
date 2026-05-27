# main.py - 主要的機器人啟動程式
"""
此模組為 Discord 機器人的主程式進入點。
負責載入環境變數、初始化核心服務 (如日誌)、定義事件攔截器，並啟動機器人。
"""

import asyncio
import os
from typing import Any

import discord
from discord.ext import commands
from dotenv import load_dotenv

# 引入抽離出去的核心日誌服務
from core.logger import setup_logging

# 1. 啟動全域日誌系統
log = setup_logging("MusicBot")

# 2. 載入環境變數與 Discord 設定
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True


# ==========================================
# 建立自訂 Bot 類別，攔截所有事件
# ==========================================
class CustomBot(commands.Bot):
    """自訂的 Discord Bot 類別，用於全域事件攔截與日誌記錄。"""

    def dispatch(self, event_name: str, /, *args: Any, **kwargs: Any) -> None:
        """分派 Discord 事件並記錄高層級的活動日誌。

        Args:
            event_name (str): Discord 事件名稱（不包含 `on_` 前綴）。
            *args (Any): 由 discord.py 轉發的事件內容（位置引數）。
            **kwargs (Any): 由 discord.py 轉發的事件內容（關鍵字引數）。

        Returns:
            None.

        Notes:
            為了保持日誌的可讀性，底層高頻率的 websocket 通訊事件將被忽略。
        """
        ignore_events = ["socket_raw_receive", "socket_raw_send", "socket_response"]

        if event_name not in ignore_events:
            log.info(f"[事件攔截] ⚡ 觸發事件: on_{event_name}")

        super().dispatch(event_name, *args, **kwargs)


# 初始化機器人實例
bot = CustomBot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready() -> None:
    """當 Discord 標記機器人為就緒狀態後，記錄啟動訊息。

    Args:
        無。

    Returns:
        None.

    Notes:
        如果 Discord 重新建立 Gateway 連線，此事件可能會再次被觸發。
    """
    log.info("====================================")
    log.info(f"登入成功！機器人 {bot.user} 已經上線。")
    log.info("全域事件監聽器已啟動。")
    log.info("====================================")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    """處理 discord.py 執行期間拋出的指令錯誤。

    Args:
        ctx (commands.Context): 呼叫指令的上下文物件。
        error (commands.CommandError): 解析或執行期間拋出的指令錯誤例外。

    Returns:
        None.

    Notes:
        對於未知的指令，會發送友善的 Discord 訊息提示使用者；其他錯誤則會記錄包含
        traceback 的完整資訊以便進行後續除錯。
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❓ 未知的指令：`{ctx.message.content}`。")
        log.warning(f"未知指令嘗試: {ctx.author} 嘗試執行 {ctx.message.content}")
    else:
        log.error(f"執行指令時發生錯誤: {error}", exc_info=True)


async def load_extensions() -> None:
    """載入 `cogs` 目錄下的所有 Cog 擴充模組檔案。

    Args:
        無。

    Returns:
        None.

    Notes:
        `cogs` 目錄中的每個 `.py` 檔案都會被視為一個 discord.py 擴充功能並進行載入。
    """
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            log.info(f"✅ 已載入模組: {filename}")


async def main() -> None:
    """在非同步上下文管理器 (Context Manager) 中啟動 Discord 機器人。

    Args:
        無。

    Returns:
        None.

    Notes:
        Discord Token 會從 `.env` 檔案中載入；若遺失 Token 則會記錄嚴重錯誤並阻止啟動。
    """
    async with bot:
        await load_extensions()

        if not TOKEN:
            log.critical(
                "❌ 錯誤：找不到 DISCORD_TOKEN，請檢查 .env 檔案是否設定正確！"
            )
            return

        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        log.info("機器人系統正在啟動中...")
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("收到中斷訊號 (Ctrl+C)，機器人已安全關閉。")
