# music/services/queue_actions.py - 佇列相關音樂行為服務模組
"""
佇列相關音樂行為 (Queue-related music behaviors) 服務模組。

此模組集中管理所有針對音樂播放器「待播佇列 (Queue)」的操作邏輯。
包含檢視、清理、刪除單一曲目、隨機打亂，以及直接跳轉至特定曲目播放等功能。
"""

import random

from core.context import InteractionContext
from music.player import get_player
from music.utils import format_time


async def debug_queue(ctx: InteractionContext) -> None:
    """
    印出目前佇列狀態供開發除錯使用。

    將當前的 `player.queue` 陣列直接輸出到後端終端機 (Terminal) 的標準輸出中，
    並在 Discord 頻道回覆執行結果。主要用於開發與維護階段。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)
    print(f"目前佇列: {player.queue}")
    await ctx.send("已在終端機印出目前 Queue 的狀態。")


async def clear_queue(ctx: InteractionContext) -> None:
    """
    清空播放器的待播佇列。

    將清空所有尚未播放的歌曲，但不會影響目前正在播放的歌曲。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)
    player.queue.clear()
    await ctx.send("🗑️ 播放佇列已清空。")


async def show_queue(ctx: InteractionContext) -> None:
    """
    顯示目前的播放佇列清單。

    為避免字數超過 Discord 的單一訊息長度限制 (2000 字元)，
    此方法預設僅顯示佇列中的前 10 首歌曲，並在結尾提示剩餘的歌曲數量。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    if len(player.queue) == 0:
        return await ctx.send("目前沒有任何歌曲在佇列中。")

    # 組合前 10 首歌曲的字串，包含編號、標題與格式化後的時長
    queue_str = "\n".join(
        [
            f"{i + 1}. {song['title']} - `{format_time(song.get('duration', 0))}`"
            for i, song in enumerate(player.queue[:10])
        ]
    )

    # 若佇列超過 10 首歌，則在底部加上省略提示
    if len(player.queue) > 10:
        queue_str += f"\n... 以及其他 {len(player.queue) - 10} 首歌曲"

    await ctx.send(f"**播放佇列：**\n{queue_str}")


async def remove_from_queue(ctx: InteractionContext, index: int) -> None:
    """
    從佇列中移除指定位置的歌曲。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        index (int): 欲刪除的歌曲在佇列中的編號 (以 1 為起始基準，即 1-based index)。
    """
    if not index:
        return await ctx.send("請提供要刪除的歌曲位置。\n用法: /remove <編號>")

    player = get_player(ctx)

    if not player.queue:
        return await ctx.send("目前播放佇列是空的。")

    # 防呆：檢查輸入的索引值是否在有效範圍內
    if index < 1 or index > len(player.queue):
        return await ctx.send(
            f"無效的位置。請輸入 1 到 {len(player.queue)} 之間的數字。"
        )

    # index - 1 將 1-based index 轉換回 Python 原生的 0-based index 進行 pop 操作
    removed_song = player.queue.pop(index - 1)
    await ctx.send(f"🗑️ 已從播放清單中刪除第 {index} 首歌：{removed_song['title']}")


async def shuffle_queue(ctx: InteractionContext) -> None:
    """
    隨機打亂佇列中的歌曲順序 (Shuffle)。

    使用 `random.shuffle` 對當前的等待清單進行原地 (in-place) 洗牌。
    不會影響目前正在播放的歌曲。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
    """
    player = get_player(ctx)

    if len(player.queue) < 2:
        return await ctx.send("佇列中歌曲太少，無法隨機播放。")

    random.shuffle(player.queue)
    await ctx.send("🔀 佇列已隨機打亂。")


async def jump_to_index(ctx: InteractionContext, index: int) -> None:
    """
    立即跳轉並播放佇列中的特定歌曲。

    此方法的實作邏輯為：
    1. 將指定編號的歌曲從佇列中抽離出來。
    2. 插入到佇列的最前端 (順位第 0 位)。
    3. 強制中斷目前的播放音訊。
    後續播放器的主迴圈 (Event Loop) 會自動抓取佇列最前端的這首歌來播放。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        index (int): 欲跳轉的目標歌曲編號 (1-based index)。
    """
    if not index:
        return await ctx.send("請指定要跳轉的有效歌曲編號。")

    player = get_player(ctx)

    # 防呆：檢查輸入的索引值是否在有效範圍內
    if index < 1 or index > len(player.queue):
        return await ctx.send("指定的歌曲編號無效。")

    # 將目標歌曲抽出並放到最前面
    target_song = player.queue.pop(index - 1)
    player.queue.insert(0, target_song)

    # 若目前有歌曲正在播放，則將其停止，觸發下一首 (即我們剛才插入的目標歌曲) 的播放
    if ctx.voice_client and (
        ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
    ):
        ctx.voice_client.stop()

    await ctx.send(f"🦘 已跳轉至第 {index} 首。")
