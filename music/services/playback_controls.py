# music/services/playback_controls.py - 音樂播放控制行為服務模組
"""
音樂播放控制行為 (Playback control behaviors) 服務模組。

此模組封裝了所有與音樂播放進度、狀態控制相關的邏輯。
透過操作 Discord 的 VoiceClient (如 pause, resume, stop) 以及
內部自訂的播放器實例 (Player) 的佇列與歷史紀錄，來實現完整的音樂控制功能。
"""

from core.context import InteractionContext
from music.player import get_existing_player
from music.utils import format_time


async def pause_playback(ctx: InteractionContext) -> None:
    """
    暫停當前正在播放的音樂。

    除了呼叫底層 Discord 語音客戶端的 `pause()` 之外，還會同步更新
    播放器內部的時間計數器 (pause_time)，以確保動態歌詞與進度條的時間軸準確。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        player = get_existing_player(ctx)
        if player:
            player.pause_time()
            await player.refresh_public_panel("⏸️ 已暫停播放。")
        await ctx.send("⏸️ 已暫停播放。")


async def resume_playback(ctx: InteractionContext) -> None:
    """
    繼續播放已暫停的音樂。

    呼叫底層 Discord 語音客戶端的 `resume()`，並同步喚醒
    播放器內部的時間計數器 (resume_time)，讓時間軸繼續推進。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        player = get_existing_player(ctx)
        if player:
            player.resume_time()
            await player.refresh_public_panel("▶️ 已繼續播放。")
        await ctx.send("▶️ 已繼續播放。")


async def stop_playback(ctx: InteractionContext) -> None:
    """
    停止播放音樂並清理播放器資源。

    此方法會停止目前音訊、清空佇列與歷史紀錄、刪除或停用固定播放器面板，
    並中斷語音連線以釋放 FFmpeg 與 yt-dlp 相關資源。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_existing_player(ctx)
    if not player:
        return await ctx.send("❌ 目前沒有可停止的播放器。")

    await player.shutdown()
    await ctx.send("⏹️ 播放器已停止並釋放資源。")


async def skip_track(ctx: InteractionContext) -> None:
    """
    跳過當前歌曲。

    透過強制呼叫 `ctx.voice_client.stop()` 來觸發 Discord 語音客戶端的
    'after' 回呼函式 (Callback)。播放器主迴圈偵測到停止後，會自動從佇列
    中取出下一首歌曲進行播放。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_existing_player(ctx)
    if player and player.request_next_track():
        await ctx.send("⏭️ 已跳過歌曲！")
    else:
        await ctx.send("目前沒有播放任何歌曲可以跳過。")


async def play_previous(ctx: InteractionContext) -> None:
    """
    切換回上一首播放的歌曲。

    此方法會操作播放器的佇列 (Queue) 與歷史紀錄 (History)：
    1. 從歷史紀錄彈出 (Pop) 上一首歌曲。
    2. 將當前正在播放的歌曲推回 (Insert) 待播佇列的最前端。
    3. 將彈出的歷史歌曲設為當前歌曲，並中斷當前播放以觸發換歌機制。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_existing_player(ctx)
    if not player:
        return await ctx.send("目前沒有播放器紀錄。")

    if not player.request_previous_track():
        return await ctx.send("沒有上一首歌曲的紀錄。")

    await ctx.send("⏮️ 播放上一首歌曲。")


async def seek_track(ctx: InteractionContext, seconds: int) -> None:
    """
    將當前歌曲跳轉至指定的時間點 (秒數)。

    由於 Discord `VoiceClient` 不支援直接熱跳轉 (Hot Seeking)，此方法的實作方式為：
    設定播放器的 `seek_offset`，將當前歌曲重新放入佇列頂端，接著中斷當前播放。
    當播放器主迴圈抓取該歌曲時，會讀取 `seek_offset` 並透過 FFmpeg 的
    `-ss` 參數從指定時間點重新開始串流。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        seconds (int): 欲跳轉的目標時間點 (以秒為單位)。
    """
    if seconds is None or seconds < 0:
        return await ctx.send("請指定要跳轉的有效時間 (秒數)。")

    player = get_existing_player(ctx)
    if not player:
        return await ctx.send("目前沒有歌曲正在播放。")

    if not player.current or not ctx.voice_client:
        return await ctx.send("目前沒有歌曲正在播放。")

    if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        return await ctx.send("目前沒有歌曲正在播放。")

    # 強制停止目前音訊，觸發主迴圈以新的偏移量重新播放該歌曲
    if not player.request_seek(seconds):
        return await ctx.send("目前沒有歌曲可以跳轉。")

    await player.refresh_public_panel(f"⏩ 已跳轉至 {format_time(seconds)}。")
    await ctx.send(f"⏩ 已跳轉至 {format_time(seconds)}。")
