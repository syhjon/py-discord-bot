# music/services/playlists.py - 提供播放清單儲存路徑的管理輔助函式
import os


def get_playlists_dir(base_file: str) -> str:
    """取得播放清單儲存目錄的路徑。

    Args:
        base_file (str): 用於計算相對路徑的起始基準檔案路徑。

    Returns:
        str: 專案層級 storage/playlists 目錄的絕對路徑。

    Notes:
        播放清單目錄被設定在 `music` 套件之外，以確保使用者資料與原始程式碼分離，
        便於維護與備份。
    """
    return os.path.abspath(
        os.path.join(
            os.path.dirname(base_file),
            "..",
            "storage",
            "playlists",
        )
    )


def ensure_playlists_dir(playlists_dir: str) -> None:
    """確保播放清單儲存目錄存在，若不存在則自動建立。

    Args:
        playlists_dir (str): 儲存播放清單 JSON 檔案的目錄路徑。

    Returns:
        None.

    Notes:
        此函式設計為在 Cog 初始化時安全呼叫，以確保後續的讀寫操作不會失敗。
    """
    os.makedirs(playlists_dir, exist_ok=True)
