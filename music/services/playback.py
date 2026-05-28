# music/services/playback.py - 集中處理點歌與插播的生命週期與資源管理
import asyncio
import gc
from typing import Any

import discord

from core.context import InteractionContext
from domain import IMusicSearchService
from music.services.youtube import fetch_song_data, extract_info
from music.ui import SongSelect


async def process_track_request(
    ctx: InteractionContext,
    query: str,
    search_service: IMusicSearchService | Any,
    is_cutin: bool = False,
    fetch_count: int = 1,
    use_select_menu: bool = False,
) -> None:
    """統一處理歌曲搜尋與加入佇列的邏輯，具備嚴格的資源生命週期管理。

    Args:
        ctx (InteractionContext): Discord 斜線指令互動上下文。
        query (str): 使用者輸入的搜尋關鍵字或網址。
        search_service (IMusicSearchService | Any): 音樂搜尋服務；也相容舊版 yt-dlp 實例。
        is_cutin (bool): 是否為插播模式（強制移動到佇列最前方並立即播放）。
        fetch_count (int): 要向 yt-dlp 請求的結果數量。
        use_select_menu (bool): 是否使用 UI 下拉選單供使用者選擇 (True 代表為 song 指令)。

    Returns:
        None.
    """
    from music.player import get_player

    if not query:
        return await ctx.send("❌ 請提供歌曲名稱或 YouTube 網址。")

    voice_state = getattr(ctx.author, "voice", None)
    if not voice_state:
        return await ctx.send("❌ 您必須先加入一個語音頻道。")

    if not ctx.voice_client:
        await voice_state.channel.connect()

    msg = await ctx.send(f"🔍 正在搜尋並處理歌曲：`{query}` ...")
    player = get_player(ctx)

    fetch_task = None
    raw_data = None

    try:
        loop = asyncio.get_running_loop()
        uses_search_service = hasattr(search_service, "fetch_song_data")
        if uses_search_service:
            fetch_task = loop.create_task(
                search_service.fetch_song_data(query, fetch_count)
            )
        else:
            fetch_task = loop.create_task(
                fetch_song_data(search_service, query, fetch_count)
            )

        # 這裡將逾時稍微放寬到 20 秒，因為如果 fetch_count=10 會抓得比較久
        raw_data = await asyncio.wait_for(fetch_task, timeout=20.0)

        if not raw_data:
            return await msg.edit(content="❌ 找不到相關歌曲！")

        # ========================
        # UI 選單模式 (/song)
        # ========================
        if use_select_menu and len(raw_data) > 1:
            # 建立互動式選單，設定 20 秒逾時
            view = discord.ui.View(timeout=20.0)
            view.add_item(SongSelect(raw_data, player, ctx))

            # 定義逾時觸發的自我銷毀邏輯
            async def on_timeout():
                try:
                    # 將原本的訊息修改為過期提示，並移除下拉選單元件 (view=None)
                    # 若您希望連訊息本身都完全消失，可以將這裡改為： await msg.delete()
                    await msg.edit(
                        content="⏳ 點歌選單已過期 (超過 20 秒未選擇)。請重新輸入指令。",
                        view=None,
                    )
                except discord.HTTPException:
                    # 避免訊息已經被使用者手動刪除而導致報錯
                    pass

            # 綁定逾時事件
            view.on_timeout = on_timeout

            await msg.edit(
                content="請從下列選單中選擇你要播放的歌曲 (20 秒後自動取消)：",
                view=view,
            )
            return

        # ========================
        # 直接播放模式 (/quick / /cutin / 結果僅有1首)
        # ========================
        if uses_search_service:
            song_info = search_service.extract_info(raw_data[0])
        else:
            song_info = extract_info(raw_data[0])

        if is_cutin:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if player.current:
                    player.queue.insert(0, player.current)
                player.queue.insert(0, song_info)
                ctx.voice_client.stop()
                await msg.edit(
                    content=f"🎶 已將 **{song_info['title']}** 插播並開始播放！原歌曲已排到下一首。"
                )
            else:
                await player.add_to_queue(song_info, ctx)
                await msg.edit(content=f"🎶 正在播放 **{song_info['title']}**。")
        else:
            # 這裡不使用 msg.edit 是因為 add_to_queue 會自己發送排版精美的 Embed，
            # 為了畫面乾淨，直接把 "正在搜尋..." 的提示訊息刪掉即可。
            await msg.delete()
            await player.add_to_queue(song_info, ctx)

    except asyncio.TimeoutError:
        if fetch_task and not fetch_task.done():
            fetch_task.cancel()
        await msg.edit(content="⚠️ 搜尋超時！已經強制終止該程序以釋放系統資源。")

    except asyncio.CancelledError:
        if fetch_task and not fetch_task.done():
            fetch_task.cancel()

    except Exception as e:
        await msg.edit(content=f"⚠️ 處理歌曲時發生錯誤：`{e}`")

    finally:
        # 強制資源回收
        if raw_data is not None:
            del raw_data
        if fetch_task is not None:
            del fetch_task
        gc.collect()
