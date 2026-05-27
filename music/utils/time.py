# music/utils/time.py - 處理播放時間格式化與純文字進度條產生
from typing import Union


def format_time(seconds: Union[int, float, str, None]) -> str:
    """將秒數格式化為 `分鐘:秒數` 的字串。

    Args:
        seconds (Union[int, float, str, None]): 數值秒數、`None`，或是特殊字串 `未知時長`。

    Returns:
        str: 格式化後的時間字串（例如 "3:05"），若時長未知則回傳 `未知`。

    Notes:
        此函式可向下相容，處理舊版佇列資料中使用的 `未知時長` 標記字串。
    """
    if seconds is None or seconds == "未知時長":
        return "未知"

    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def create_progress_bar(
    current_time: Union[int, float], duration: Union[int, float, str, None]
) -> str:
    """為當前播放的音軌建立純文字進度條。

    Args:
        current_time (Union[int, float]): 當前播放位置（秒數）。
        duration (Union[int, float, str, None]): 音軌總時長（秒數）、`None`，或是特殊字串 `未知時長`。

    Returns:
        str: 包含 20 個字元長度的進度條字串，並帶有當前位置的圖示標記。

    Notes:
        當音軌時長未知或為零時（例如直播串流），會回傳預設的防呆進度條，以避免發生除以零的錯誤 (ZeroDivisionError)。
    """
    if duration == 0 or duration is None or duration == "未知時長":
        return "━" * 19 + "🔘"

    total_bars = 20
    # 計算當前位置百分比並對應到 20 格
    current_bar = round((current_time / duration) * total_bars)
    current_bar = min(max(current_bar, 0), total_bars)

    if current_bar == total_bars:
        return "━" * 19 + "🔘"

    return "━" * current_bar + "🔘" + "─" * (total_bars - current_bar - 1)
