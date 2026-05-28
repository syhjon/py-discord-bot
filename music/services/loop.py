# music/services/loop.py - 音樂播放循環模式行為服務
"""
音樂播放循環模式行為 (Repeat mode behaviors) 服務模組。

此模組負責處理設定與切換音樂播放器循環模式的核心邏輯。
它將使用者輸入的文字指令轉換為播放器內部理解的狀態代碼 (0: 關閉, 1: 單曲, 2: 佇列)。
"""

from core.context import InteractionContext
from music.player import get_player


async def set_loop_mode(ctx: InteractionContext, mode: str) -> None:
    """
    設定當前伺服器音樂播放器的循環模式。

    根據使用者傳入的字串參數，切換播放器的 `loop_mode` 屬性，
    並回傳對應的設定成功訊息或錯誤提示。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        mode (str): 欲設定的循環模式名稱。支援的值包含：
            - "off": 關閉循環
            - "song": 單曲循環
            - "all" 或 "queue": 整個播放佇列循環
    """
    # 取得當前伺服器綁定的音樂播放器實例
    player = get_player(ctx)

    # 將輸入轉為小寫以統一格式，若未提供則預設為空字串，避免防呆判斷出錯
    mode = mode.lower() if mode else ""

    # 根據輸入字串設定對應的內部狀態代碼
    if mode == "off":
        # 0 代表關閉所有循環
        player.loop_mode = 0
    elif mode == "song":
        # 1 代表單曲循環 (重複播放當前歌曲)
        player.loop_mode = 1
    elif mode in ["all", "queue"]:
        # 2 代表佇列循環 (當前歌曲播完後移至佇列尾端)
        player.loop_mode = 2
    else:
        # 若輸入不符合預期，則提早返回並發送錯誤提示
        return await ctx.send("請指定循環模式：`off`, `song`, `all`, 或 `queue`。")

    # 根據設定好的內部狀態代碼，轉換為要顯示給使用者看的人類可讀字串
    mode_str = (
        "關閉"
        if player.loop_mode == 0
        else "單曲循環" if player.loop_mode == 1 else "佇列循環"
    )

    # 傳送設定成功的確認訊息
    await ctx.send(f"🔁 循環模式已設定為：{mode_str}。")
