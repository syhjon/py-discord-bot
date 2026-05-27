# music/ui/__init__.py - 匯出供 Music Cog 使用的 UI 元件
from .controls import PlayerControls
from .help import HelpPagination
from .song_select import SongSelect

"""
ui 套件
-------
此套件封裝了音樂播放器的使用者介面元件，包含：
- PlayerControls: 用於控制播放流程的 UI 視圖。
- HelpPagination: 用於分頁顯示指令說明的 UI 元件。
- SongSelect: 用於歌曲搜尋結果選擇的互動式下拉選單。
"""

__all__ = ["HelpPagination", "PlayerControls", "SongSelect"]
