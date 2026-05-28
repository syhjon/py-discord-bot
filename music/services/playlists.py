# music/services/playlists.py - 播放清單儲存與載入行為服務模組
"""
播放清單儲存與載入行為 (Playlist storage and playback behaviors) 服務模組。

此模組實作了將 Discord 音樂機器人的播放佇列 (Queue) 狀態進行持久化儲存的功能。
透過將佇列匯出為 JSON 格式，使用者可以儲存自己喜歡的歌單，並在未來隨時重新載入播放。
檔案系統以使用者的 Discord ID 進行命名隔離，確保資料隱私與唯一性。
"""

import json
import os
import re

from core.context import InteractionContext


def get_playlists_dir(base_file: str) -> str:
    """
    取得播放清單儲存目錄的絕對路徑。

    Args:
        base_file (str): 用於計算相對路徑的起始基準檔案路徑 (通常為呼叫端的 __file__)。

    Returns:
        str: 專案層級 `storage/playlists` 目錄的絕對路徑。

    Notes:
        播放清單目錄被設定在 `music` 套件之外 (專案根目錄的 storage 下)，
        以確保使用者產生的資料與原始程式碼分離，便於未來維護、轉移與備份。
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
    """
    確保播放清單儲存目錄存在，若不存在則自動建立。

    Args:
        playlists_dir (str): 儲存播放清單 JSON 檔案的目錄路徑。

    Notes:
        此函式設計為在 Cog 初始化時安全呼叫，以確保後續的讀寫操作不會因
        資料夾不存在而引發 FileNotFoundError。
    """
    os.makedirs(playlists_dir, exist_ok=True)


async def save_current_queue(ctx: InteractionContext, playlist_name: str) -> None:
    """
    將目前的播放佇列儲存為使用者的專屬播放清單。

    此方法會擷取目前正在播放的歌曲，以及佇列中所有等待播放的歌曲，
    提取重要的中繼資料 (Metadata) 後，以 JSON 陣列的形式寫入本地硬碟。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        playlist_name (str): 使用者欲命名的播放清單名稱。
    """
    # 延遲匯入以避免潛在的循環依賴 (Circular Dependency)
    from music.player import get_player

    if not playlist_name:
        return await ctx.send(
            "請提供播放清單名稱。\n用法: /saveplaylist <播放清單名稱>"
        )

    player = get_player(ctx)
    # 防呆：確保有資料可以儲存
    if not player.queue and not player.current:
        return await ctx.send("目前播放佇列中沒有歌曲，無法儲存。")

    playlists_dir = os.path.join(os.getcwd(), "storage", "playlists")
    os.makedirs(playlists_dir, exist_ok=True)

    # 清洗檔名：利用 Regex 移除作業系統不允許的特殊字元，避免儲存失敗或路徑注入攻擊
    safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "_", playlist_name).strip()
    if not safe_playlist_name:
        return await ctx.send("❌ 播放清單名稱包含過多無效字元，請更換一個名稱。")

    # 檔案命名規則：使用者ID_安全檔名.json，藉此區分不同使用者的歌單
    file_path = os.path.join(
        playlists_dir, f"{ctx.author.id}_{safe_playlist_name}.json"
    )

    save_list = []

    # 優先保存當前正在播放的歌曲
    if player.current:
        save_list.append(
            {
                "name": player.current.get("title", "未知標題"),
                "url": player.current.get("webpage_url", player.current.get("url")),
                "duration": player.current.get("duration", 0),
                "uploader": player.current.get("uploader", "未知"),
                "thumbnail": player.current.get("thumbnail"),
            }
        )

    # 依序保存佇列中所有待播歌曲
    for song in player.queue:
        save_list.append(
            {
                "name": song.get("title", "未知標題"),
                "url": song.get("webpage_url", song.get("url")),
                "duration": song.get("duration", 0),
                "uploader": song.get("uploader", "未知"),
                "thumbnail": song.get("thumbnail"),
            }
        )

    try:
        # 將資料結構寫入 JSON 檔案，確保支援中文 (ensure_ascii=False)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_list, f, ensure_ascii=False, indent=2)
        await ctx.send(f"✅ 已將目前的佇列儲存為播放清單：**{playlist_name}**")
    except Exception as e:
        print(f"SavePlaylist Error: {e}")
        await ctx.send("⚠️ 儲存播放清單時發生系統錯誤，請稍後再試。")


async def play_saved_playlist(ctx: InteractionContext, playlist_name: str) -> None:
    """
    讀取並播放使用者先前儲存的播放清單。

    此方法會從本地端讀取對應的 JSON 檔案，確保機器人已連線至語音頻道後，
    將檔案中的所有歌曲批次加入至目前的播放佇列中。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        playlist_name (str): 欲載入的播放清單名稱。
    """
    from music.player import get_player

    if not playlist_name:
        return await ctx.send(
            "請提供要載入並播放的播放清單名稱。\n用法: /playplaylist <名稱>"
        )

    playlists_dir = os.path.join(os.getcwd(), "storage", "playlists")
    os.makedirs(playlists_dir, exist_ok=True)

    # 採用與儲存時相同的檔名清洗與推導邏輯，確保能精準命中檔案
    safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "_", playlist_name).strip()
    if not safe_playlist_name:
        return await ctx.send("❌ 播放清單名稱無效。")

    file_path = os.path.join(
        playlists_dir, f"{ctx.author.id}_{safe_playlist_name}.json"
    )

    if not os.path.exists(file_path):
        return await ctx.send(f"❌ 找不到名為「**{playlist_name}**」的播放清單。")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            selected_playlist = json.load(f)
    except Exception as e:
        print(f"PlayPlaylist Error: {e}")
        return await ctx.send("⚠️ 讀取播放清單時發生檔案錯誤。")

    # 驗證資料完整性
    if not selected_playlist or not isinstance(selected_playlist, list):
        return await ctx.send(f"播放清單「**{playlist_name}**」中沒有歌曲或檔案損毀。")

    # 確保使用者與機器人處於正確的語音頻道狀態
    voice_state = getattr(ctx.author, "voice", None)
    if not voice_state:
        return await ctx.send("你必須先加入一個語音頻道才能播放音樂。")

    if not ctx.voice_client:
        await voice_state.channel.connect()

    msg = await ctx.send(f"🔄 正在載入播放清單「**{playlist_name}**」...")
    player = get_player(ctx)

    # 將反序列化的 JSON 字典重組為播放器所需的 song_info 格式
    for song in selected_playlist:
        song_info = {
            "title": song.get("name", "未知標題"),
            "url": song.get("url", ""),
            "webpage_url": song.get("url", ""),
            "duration": song.get("duration", 0),
            "uploader": song.get("uploader", "未知"),
            "thumbnail": song.get("thumbnail"),
        }
        # 呼叫播放器的加入佇列方法，並設定 announce=False 以避免加入大量歌曲時洗版
        await player.add_to_queue(song_info, ctx, announce=False)

    # 所有歌曲加入完畢後更新狀態訊息
    await msg.edit(content=f"🎶 已成功將播放清單「**{playlist_name}**」加入佇列！")
