# core/config.py - 應用程式環境設定載入模組
"""
應用程式環境設定載入模組 (Application configuration loading)。

負責讀取環境變數檔案 (.env) 並將其封裝為具有型別提示 (Type Hinting)
的資料類別，以供整個應用程式安全、唯讀且一致地存取設定值。
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class BotConfig:
    """
    Discord 機器人的執行時期環境設定 (Runtime Configuration) 資料類別。

    使用 `frozen=True` 確保屬性在實例化後不可被修改 (Immutable)，
    使用 `slots=True` 則可優化記憶體使用並加快屬性存取速度。

    Attributes:
        token (Optional[str]): Discord 應用程式的 Bot Token，用於身分驗證與連線。
        guild_id (Optional[str]): 指定要同步斜線指令的 Discord 伺服器 ID。
            通常在開發階段設定，以實現指令的即時更新；若不設定則預設為全域同步。
    """

    token: Optional[str]
    guild_id: Optional[str]


def load_config() -> BotConfig:
    """
    載入環境變數並回傳型別安全的機器人設定檔物件。

    此函式會呼叫 `load_dotenv()` 來讀取專案根目錄下的 `.env` 檔案，
    接著將讀取到的環境變數注入到 `BotConfig` 資料類別中並回傳。

    Returns:
        BotConfig: 包含目前環境設定的唯讀資料類別實例。
    """
    # 載入 .env 檔案中的環境變數到 os.environ
    load_dotenv()

    # 建構並回傳設定檔實例
    return BotConfig(
        token=os.getenv("DISCORD_TOKEN"),
        guild_id=os.getenv("DISCORD_GUILD_ID"),
    )
