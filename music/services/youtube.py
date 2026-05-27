# music/services/youtube.py - YouTube 相關的服務與工具函式
import asyncio
from typing import Any, Dict, List
import yt_dlp


def create_player_ytdl() -> yt_dlp.YoutubeDL:
    """創建用於「播放」的 yt-dlp 實例。

    此實例設定較為輕量，專注於取得最佳音質的串流網址，不包含複雜的搜尋或繞過挑戰設定，
    以確保取得播放網址的速度與穩定性。

    Returns:
        yt_dlp.YoutubeDL: 配置好的 yt-dlp 實例。

    Notes:
        此實例經過優化，專門用於提取直接音訊串流網址。
    """
    return yt_dlp.YoutubeDL(
        {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "source_address": "0.0.0.0",
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0.0.0"
                )
            },
        }
    )


def create_search_ytdl() -> yt_dlp.YoutubeDL:
    """創建用於「搜尋與解析」的 yt-dlp 實例。

    此設定更為全面，包含預設搜尋 (ytsearch)、處理 HTTPS 憑證、顯示警告以及
    偽裝瀏覽器執行環境，以應對 YouTube 的防爬蟲機制。

    Returns:
        yt_dlp.YoutubeDL: 配置好且具備高相容性的 yt-dlp 實例。

    Notes:
        `default_search` 設定允許純文字輸入自動行為像 YouTube 搜尋，無需額外的指令分流。
    """
    return yt_dlp.YoutubeDL(
        {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "nocheckcertificate": False,
            "no_warnings": False,
            "default_search": "ytsearch",
            "source_address": "0.0.0.0",
            "http_headers": {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
            "js_runtimes": {"node": {}, "deno": {}},
            "extractor_args": {"youtube": ["player_client=web"]},
        }
    )


async def fetch_song_data(
    ytdl: yt_dlp.YoutubeDL, query: str, limit: int = 1
) -> List[Dict[str, Any]]:
    """非同步獲取 YouTube 歌曲資料。

    根據提供的字串進行解析。若字串為網址，則直接解析該網址；
    若為一般字串，則使用 YouTube 搜尋功能回傳最相關的結果。

    Args:
        ytdl (yt_dlp.YoutubeDL): 用來執行抓取任務的 yt-dlp 實例。
        query (str): 歌曲的 URL 網址或搜尋關鍵字。
        limit (int, optional): 預期回傳的最大結果數量。預設為 1。

    Returns:
        List[Dict[str, Any]]: 包含歌曲原始資料字典的列表。若無結果則回傳空列表。

    Notes:
        萃取程序在執行緒池中運行，確保阻塞性的 yt-dlp 任務不會凍結 Discord 事件迴圈。
    """
    loop = asyncio.get_running_loop()
    search_query = f"ytsearch{limit}:{query}" if not query.startswith("http") else query

    # 執行阻塞式操作
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(search_query, download=False)
    )

    if data and "entries" in data:
        return data["entries"][:limit]
    return [data] if data else []


def extract_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """將 yt-dlp 原始資料轉換為播放器標準格式。

    從龐大的 yt-dlp 回傳結果中，萃取出播放器與 UI (Embed) 實際需要使用的欄位，
    並提供預設值以防止 Key Error。

    Args:
        data (Dict[str, Any]): 從 yt-dlp 解析出來的單一歌曲原始字典資料。

    Returns:
        Dict[str, Any]: 格式化後的歌曲資訊字典，包含 url, webpage_url, title, duration, uploader, thumbnail。

    Notes:
        遺失的選填欄位會自動補上預設值，以確保程式穩定性。
    """
    return {
        "url": data["url"],
        "webpage_url": data.get("webpage_url", data.get("url")),
        "title": data.get("title", "未知曲目"),
        "duration": data.get("duration", 0),
        "uploader": data.get("uploader", "未知"),
        "thumbnail": (
            data.get("thumbnails", [{"url": ""}])[0]["url"]
            if data.get("thumbnails")
            else None
        ),
    }


class YouTubeServiceMixin:
    """提供 YouTube 搜尋與資料解析的混合類別 (Mixin)。

    設計供 Discord Cog 繼承使用，統一管理與 YouTube 互動的邏輯介面。
    繼承此類別的實例必須在 `__init__` 中定義 `self.ytdl`。
    """

    async def fetch_song_data(self, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """呼叫底層 fetch_song_data 進行搜尋。

        Args:
            query (str): 歌曲的 URL 網址或搜尋關鍵字。
            limit (int, optional): 預期回傳的最大結果數量。預設為 1。

        Returns:
            List[Dict[str, Any]]: 歌曲原始資料列表。

        Notes:
            此方法將任務委派給模組級輔助函式，保持指令 Mixin 的簡潔性。
        """
        return await fetch_song_data(self.ytdl, query, limit)

    def extract_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """呼叫底層 extract_info 進行資料格式化。

        Args:
            data (Dict[str, Any]): yt-dlp 原始字典資料。

        Returns:
            Dict[str, Any]: 播放器標準格式字典。

        Notes:
            此包裝器為所有指令 Mixin 提供穩定的 `self.extract_info(...)` API。
        """
        return extract_info(data)
