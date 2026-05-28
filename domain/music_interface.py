# domain/music_interface.py - 音樂相關服務介面定義模組
"""
音樂相關服務介面定義模組 (Music-related service interface definitions)。

此模組定義了應用程式中與音樂搜尋、資料擷取相關服務所必須遵循的抽象協定 (Protocol)。
透過定義介面，確保了音樂播放展示層 (Cogs) 與具體的搜尋引擎實作 (例如 YouTube 搜尋)
之間的解耦 (Decoupling)。
"""

from typing import Any, Dict, List, Protocol


class IMusicSearchService(Protocol):
    """
    音樂搜尋與資料格式化服務的抽象能力介面 (Protocol)。

    定義了音樂機器人取得與解析音源資料所需的標準合約 (Contract)，任何提供
    音樂搜尋功能的具體實作 (例如 YouTubeSearchService) 皆應滿足此介面。
    """

    # 音訊下載與解析引擎實例 (例如 yt-dlp 的實例)。
    # 宣告為 Any 以保持介面的彈性，具體實作端需負責管理此引擎的生命週期與設定。
    ytdl: Any

    async def fetch_song_data(self, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        依據搜尋字串或網址取得候選歌曲資料。

        此為非同步方法，負責向外部服務 (如 YouTube API 或網頁抓取) 發起搜尋
        或詮釋資料 (Metadata) 的請求，並回傳符合條件的歌曲列表。

        Args:
            query (str): 使用者輸入的搜尋關鍵字，或特定的影片/播放清單網址。
            limit (int, optional): 預期回傳的搜尋結果數量上限。預設為 1。

        Returns:
            List[Dict[str, Any]]: 包含一至多筆原始歌曲資訊字典的列表。
                若無符合的搜尋結果，應回傳空列表。
        """
        ...

    def extract_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將外部來源的原始歌曲資料轉換為系統內部播放器使用的標準格式。

        負責過濾、清洗外部 API 回傳的繁雜原始資料，提取出內部播放引擎實際
        需要的關鍵欄位 (例如：串流網址、標題、時長、縮圖、上傳者等)，以確保
        後續播放邏輯的穩定運作。

        Args:
            data (Dict[str, Any]): 由 `fetch_song_data` 或底層音訊引擎回傳的單筆原始資料。

        Returns:
            Dict[str, Any]: 經過清洗與標準化後的內部格式歌曲資訊字典。
        """
        ...
