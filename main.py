# main.py - Discord 機器人應用程式入口點
"""
Discord 機器人應用程式入口點 (Entry Point)。

負責初始化設定檔、日誌系統、建立 Bot 實例，並註冊所需的各項外部服務
（例如 Gemini AI 服務與 YouTube 搜尋服務），最後啟動非同步的 Discord 連線。
"""

import asyncio

from core.bot import create_bot
from core.config import load_config
from core.logger import setup_logging
from services import GeminiService, YouTubeSearchService

# 載入環境設定檔
config = load_config()

# 設定日誌系統，定義記錄器名稱為 "MusicBot"
log = setup_logging("MusicBot")

# 建立 Discord Bot 實例
bot = create_bot(
    config=config,
    logger=log,
)
# ====================================
# 註冊依賴服務 (Dependency Injection)
# ====================================
# 註冊 AI 服務提供者 (Gemini)
bot.services.register_ai_service(GeminiService())
# 註冊音樂搜尋服務提供者 (YouTube)
bot.services.register_music_search_service(YouTubeSearchService())


async def main() -> None:
    """
    啟動 Discord 機器人的主要非同步函式。

    使用非同步上下文管理器 (Async Context Manager) 來確保 Bot 的啟動與關閉
    皆能妥善處理資源釋放。會檢查環境變數中是否存在 Discord Token，
    若無則記錄嚴重錯誤並終止執行。
    """
    async with bot:
        # 驗證 Discord Token 是否存在
        if not config.token:
            log.critical(
                "❌ 錯誤：找不到 DISCORD_TOKEN，請檢查 .env 檔案是否設定正確！"
            )
            return

        # 使用 Token 啟動 Bot 實例
        await bot.start(config.token)


if __name__ == "__main__":
    try:
        log.info("機器人系統正在啟動中...")
        # 執行主要的非同步事件迴圈
        asyncio.run(main())
    except KeyboardInterrupt:
        # 捕捉使用者中斷訊號 (Ctrl+C)，確保優雅關閉 (Graceful Shutdown)
        log.info("收到中斷訊號 (Ctrl+C)，機器人已安全關閉。")
