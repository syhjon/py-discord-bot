# services/youtube_service.py - YouTube 搜尋與歌曲資料轉換服務
"""
YouTube 搜尋與歌曲資料轉換服務模組 (Concrete YouTube search service implementation)。

此模組提供了 `domain.IMusicSearchService` 介面的具體實作，封裝了對 `yt-dlp` 的操作，
負責向 YouTube 發起搜尋請求，並將回傳的原始資料轉換為系統內部播放器所使用的標準格式。
透過這種設計，未來若要抽換搜尋引擎 (例如改用 Spotify API)，只需實作新的 Service 即可，
完全不需要更動播放器或指令展示層的邏輯。
"""

from typing import Any, Dict, List, Optional

import yt_dlp

from music.services.youtube import create_search_ytdl
from music.services.youtube import extract_info as extract_song_info
from music.services.youtube import fetch_song_data as fetch_youtube_song_data


class YouTubeSearchService:
    """
    YouTube 搜尋與歌曲資料轉換服務。

    作為領域層 `IMusicSearchService` 的具體實作類別。負責管理 `yt_dlp` 引擎實例，
    並提供非同步的資料獲取與同步的資料清洗 (Data Cleansing) 功能。
    """

    def __init__(self, ytdl: Optional[yt_dlp.YoutubeDL] = None) -> None:
        """
        初始化 YouTube 搜尋服務。

        Args:
            ytdl (Optional[yt_dlp.YoutubeDL], optional): 外部注入的 yt-dlp 實例。
                若未提供，則會呼叫 `create_search_ytdl()` 自動建立一個專為快速搜尋
                (不下載實際音訊檔) 所最佳化的新實例。預設為 None。
        """
        self.ytdl = ytdl or create_search_ytdl()

    async def fetch_song_data(self, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        依據搜尋字串或網址取得 YouTube 候選歌曲資料。

        此為非同步方法，會委託 (Delegate) 給底層的 `fetch_youtube_song_data`
        函式執行實際的非同步網路請求，以避免在獲取資料時阻塞 (Block) Discord 機器人的主事件迴圈。

        Args:
            query (str): 使用者輸入的搜尋關鍵字，或特定的 YouTube 影片/播放清單網址。
            limit (int, optional): 預期回傳的搜尋結果數量上限。預設為 1。

        Returns:
            List[Dict[str, Any]]: 包含一至多筆 YouTube 原始影片資訊字典的列表。
        """
        return await fetch_youtube_song_data(self.ytdl, query, limit)

    def extract_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 yt-dlp 取得的原始資料轉換成播放器內部使用的標準格式。

        委託底層的 `extract_song_info` 進行資料過濾，從高達數百個欄位的原始 YouTube
        回傳資料中，萃取出如串流網址 (URL)、標題、時長、上傳者與縮圖等播放器實際需要的關鍵欄位。

        Args:
            data (Dict[str, Any]): 由 yt-dlp 回傳的單筆原始影片資料字典。

        Returns:
            Dict[str, Any]: 經過格式化與清洗後的系統內部標準歌曲資訊字典。
        """
        return extract_song_info(data)
