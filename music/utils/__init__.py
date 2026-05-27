# music/utils/__init__.py - 匯出音樂模組共用的工具函式
"""
此模組為 `music.utils` 套件的初始化檔案。

負責集中匯出與音樂播放相關的共用工具函式（如時間格式化、進度條產生），
讓外部模組能夠以更簡潔的路徑引入這些工具，同時隱藏底層的實作細節。

範例：
    ```python
    from music.utils import format_time, create_progress_bar
    ```
"""

from .time import create_progress_bar, format_time

# 限制 `from music.utils import *` 時對外暴露的介面
__all__ = ["create_progress_bar", "format_time"]
