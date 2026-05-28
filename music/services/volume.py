# music/services/volume.py - 音量控制行為服務模組
"""
音量控制行為 (Volume behaviors) 服務模組。

此模組負責處理音樂播放器所有與音量相關的狀態變更。
透過修改自訂 Player 實例的音量屬性，並即時同步到 Discord 語音客戶端
(VoiceClient) 的音訊來源 (Audio Source)，以達成即時改變音量的效果。
"""

from core.context import InteractionContext
from music.player import get_player


async def set_volume(ctx: InteractionContext, vol: int) -> None:
    """
    設定音樂播放器的絕對音量。

    將使用者輸入的百分比 (0~100) 轉換為 Discord 內部使用的浮點數比例 (0.0~1.0)，
    並即時套用到目前正在播放的音訊來源上。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        vol (int): 目標音量百分比 (需介於 0 到 100 之間)。
    """
    # 防呆：確保輸入值在有效範圍內
    if vol is None or vol < 0 or vol > 100:
        return await ctx.send("請指定 0 到 100 之間的有效音量值。")

    player = get_player(ctx)
    # 將百分比轉換為浮點數 (例如 50 -> 0.5)
    player.volume = vol / 100.0

    # 若目前有音訊正在播放，則即時更新 PCMVolumeTransformer 的音量屬性
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = player.volume

    await ctx.send(f"🔊 音量已設定為 {vol}%。")


async def increase_volume(ctx: InteractionContext) -> None:
    """
    將目前的音量提高 10%。

    以 0.1 (10%) 為單位遞增，並使用 `min()` 確保音量不會超過上限 (1.0)。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)
    # 計算新音量，上限為 1.0 (100%)
    new_vol = min(player.volume + 0.1, 1.0)
    player.volume = new_vol

    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = player.volume

    await ctx.send(f"🔊 音量已增加至 {int(new_vol * 100)}%。")


async def decrease_volume(ctx: InteractionContext) -> None:
    """
    將目前的音量降低 10%。

    以 0.1 (10%) 為單位遞減，並使用 `max()` 確保音量不會低於下限 (0.0)。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)
    # 計算新音量，下限為 0.0 (0%)
    new_vol = max(player.volume - 0.1, 0.0)
    player.volume = new_vol

    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = player.volume

    await ctx.send(f"🔉 音量已降低至 {int(new_vol * 100)}%。")


async def check_volume(ctx: InteractionContext) -> None:
    """
    查詢並顯示目前的播放音量。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)
    await ctx.send(f"🔊 目前音量為：{int(player.volume * 100)}%")


async def mute(ctx: InteractionContext) -> None:
    """
    將音樂播放器靜音。

    此方法會先將目前的音量暫存到播放器的 `previous_volume` 屬性中，
    接著將實際播放音量設為 0.0。這樣未來解除靜音時就能恢復原本的設定。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    if player.volume > 0:
        # 暫存當前音量並設為 0
        player.previous_volume = player.volume
        player.volume = 0.0

        # 即時套用至音訊來源
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = 0.0

        await ctx.send("🔇 機器人已靜音。")
    else:
        await ctx.send("🔇 機器人已經是靜音狀態。")


async def unmute(ctx: InteractionContext) -> None:
    """
    解除靜音並恢復先前的音量。

    檢查是否有暫存的 `previous_volume`，若有則還原該數值，並清除暫存狀態。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    # 確保當前是靜音狀態且存在先前的音量紀錄
    if player.volume == 0.0 and player.previous_volume is not None:
        # 恢復音量
        player.volume = player.previous_volume

        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume

        # 清除暫存
        player.previous_volume = None
        await ctx.send("🔊 機器人已取消靜音。")
    elif player.volume > 0:
        await ctx.send("🔊 機器人目前不是靜音狀態。")
