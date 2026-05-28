# music/services/playback_controls.py - 音樂播放控制行為服務模組
"""
音樂播放控制行為 (Playback control behaviors) 服務模組。

此模組封裝了所有與音樂播放進度、狀態控制相關的邏輯。
透過操作 Discord 的 VoiceClient (如 pause, resume, stop) 以及
內部自訂的播放器實例 (Player) 的佇列與歷史紀錄，來實現完整的音樂控制功能。
"""

from core.context import InteractionContext
from music.player import get_player, players
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
        get_player(ctx).pause_time()
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
        get_player(ctx).resume_time()
        await ctx.send("▶️ 已繼續播放。")


async def stop_playback(ctx: InteractionContext) -> None:
    """
    停止播放音樂 (實質為凍結狀態的暫停)。

    此處的設計選擇不直接清空佇列 (Queue) 或中斷連線，而是透過暫停來達成
    「停止但保留狀態」的效果。讓使用者可以在停止後，隨時恢復原本的播放清單。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            # 確保該伺服器的播放器存在才呼叫 pause_time
            if ctx.guild.id in players:
                players[ctx.guild.id].pause_time()
            await ctx.send("⏹️ 播放已停止，目前歌曲與後續佇列已完整保留。")
        elif ctx.voice_client.is_paused():
            await ctx.send("🎵 音樂目前已經是停止狀態。")
        else:
            await ctx.send("❌ 目前沒有任何歌曲正在播放。")
    else:
        await ctx.send("❌ 機器人目前不在語音頻道中。")


async def skip_track(ctx: InteractionContext) -> None:
    """
    跳過當前歌曲。

    透過強制呼叫 `ctx.voice_client.stop()` 來觸發 Discord 語音客戶端的
    'after' 回呼函式 (Callback)。播放器主迴圈偵測到停止後，會自動從佇列
    中取出下一首歌曲進行播放。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    if ctx.voice_client and (
        ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
    ):
        ctx.voice_client.stop()
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
    player = get_player(ctx)

    if not player.history:
        return await ctx.send("沒有上一首歌曲的紀錄。")

    # 取出上一首歌
    last_song = player.history.pop()

    # 將現在這首歌放回佇列的第一順位，以便未來還能播放到
    if player.current:
        player.queue.insert(0, player.current)

    # 將上一首歌指定為準備播放的目標
    player.current = last_song

    # 中斷當前播放音訊，觸發 Player 主迴圈讀取新的 current 歌曲
    if ctx.voice_client and (
        ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
    ):
        ctx.voice_client.stop()

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

    player = get_player(ctx)

    if not player.current or not ctx.voice_client or not ctx.voice_client.is_playing():
        return await ctx.send("目前沒有歌曲正在播放。")

    # 設定跳轉的秒數偏移量
    player.seek_offset = seconds

    # 將當前歌曲重新放回佇列第一順位
    player.queue.insert(0, player.current)

    # 強制停止目前音訊，觸發主迴圈以新的偏移量重新播放該歌曲
    ctx.voice_client.stop()

    await ctx.send(f"⏩ 已跳轉至 {format_time(seconds)}。")
