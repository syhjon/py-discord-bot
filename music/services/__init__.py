# music/services/__init__.py - 匯出供 Music Cog 使用的服務輔助模組
from .gemini import GeminiService
from .playlists import ensure_playlists_dir, get_playlists_dir
from .youtube import YouTubeServiceMixin, create_player_ytdl, create_search_ytdl
from .playback import process_track_request

"""
services 套件
-----------
此套件整合了與音樂播放相關的外部服務與工具邏輯，包括：
- GeminiService: 用於處理 AI 相關的音樂分析或互動。
- playlists: 負責個人播放清單的儲存與路徑管理。
- youtube: 封裝 YT-DLP 相關的播放器與搜尋設定。
- playback: 集中處理點歌與插播的生命週期與資源管理，確保在網路延遲或意外中斷時不會產生殭屍進程佔用伺服器資源。
"""

__all__ = [
    "GeminiService",
    "YouTubeServiceMixin",
    "create_player_ytdl",
    "create_search_ytdl",
    "ensure_playlists_dir",
    "get_playlists_dir",
    "process_track_request",
]
