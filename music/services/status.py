# music/services/status.py - 音樂播放狀態與進度顯示服務模組
"""
音樂播放狀態與進度行為 (Now playing and progress behaviors) 服務模組。

此模組負責將音樂播放器的內部狀態視覺化。
包含了查詢目前正在播放的歌曲資訊、繪製文字進度條 (Progress Bar)，
以及統整播放器整體參數 (如音量、播放狀態、循環模式與待播數量) 的呈現邏輯。
"""

import discord

from core.context import InteractionContext
from music.player import get_player
from music.utils import create_progress_bar, format_time


async def show_nowplaying(ctx: InteractionContext) -> None:
    """
    顯示目前播放中的歌曲詳細資訊與播放器整體狀態。

    此方法會擷取當前播放的歌曲資料，結合播放進度條，以及
    當前的播放設定 (音量、循環模式、暫停狀態等)，封裝成一個
    Discord Embed 發送給使用者。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    # 防呆：確認目前是否有歌曲正在播放
    if not player.current:
        return await ctx.send("目前沒有任何歌曲正在播放。")

    # 取得當前播放時間與總時長
    current_time = player.get_current_time()
    duration = player.current.get("duration") or 0

    # 產生文字進度條與格式化的時長字串 (例如 "03:45")
    progress_bar = create_progress_bar(current_time, duration)
    duration_display = format_time(duration) if duration > 0 else "未知"

    # 建構基礎的 Embed 物件
    embed = discord.Embed(
        title=f"🎶 現在正在播放：**{player.current['title']}**",
        url=player.current.get("webpage_url", ""),
        color=discord.Color.blue(),
    )

    # 設定 Embed 的描述區塊，放入進度條與來源網址
    source_url = player.current.get("webpage_url", "未知")
    embed.description = (
        f"`{format_time(current_time)}` {progress_bar} "
        f"`{duration_display}`\n來源：{source_url}"
    )

    # 判斷目前的語音客戶端是處於播放還是暫停狀態
    play_state = (
        "⏸️ 暫停中"
        if ctx.voice_client and ctx.voice_client.is_paused()
        else "▶️ 播放中"
    )

    # 將內部的整數狀態代碼轉換為人類可讀的循環模式字串
    loop_str = "關閉"
    if player.loop_mode == 1:
        loop_str = "🔂 單曲循環"
    elif player.loop_mode == 2:
        loop_str = "🔁 佇列循環"

    # 組合播放器的綜合狀態資訊
    status_text = (
        f"**播放狀態：** {play_state}\n"
        f"**播放音量：** 🔊 {int(player.volume * 100)}%\n"
        f"**輪播模式：** {loop_str}\n"
        f"**待播歌曲：** 📜 {len(player.queue)} 首"
    )

    # 將狀態資訊加入 Embed 欄位中，並以非並排 (inline=False) 的方式呈現
    embed.add_field(name="📊 播放器目前狀態", value=status_text, inline=False)

    await ctx.send(embed=embed)


async def show_progress(ctx: InteractionContext) -> None:
    """
    僅顯示目前播放中歌曲的精簡版進度條。

    相較於 `show_nowplaying`，此方法提供一個更簡潔的介面，
    僅包含歌曲名稱與進度條，適合只想快速確認播放進度的使用者。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    # 防呆：確認目前是否有歌曲正在播放
    if not player.current:
        return await ctx.send("目前沒有任何歌曲正在播放。")

    # 取得時間資訊並建立進度條
    current_time = player.get_current_time()
    duration = player.current.get("duration", 0)
    progress_bar = create_progress_bar(current_time, duration)

    # 建構精簡版的 Embed 物件
    embed = discord.Embed(
        title=f"🎶 {player.current['title']}", color=discord.Color.blue()
    )
    embed.description = (
        f"`{format_time(current_time)}` {progress_bar} `{format_time(duration)}`"
    )

    await ctx.send(embed=embed)
