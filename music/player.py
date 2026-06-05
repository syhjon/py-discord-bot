# music/player.py - 管理播放佇列、語音播放、循環模式、固定播放器面板與資源清理
import asyncio
import gc
import logging
import time
from typing import Any

import discord

from core.context import InteractionContext
from music.services import create_player_ytdl
from music.ui import PlayerControls
from music.utils import create_progress_bar, format_time

log = logging.getLogger("MusicBot")


class MusicPlayer:
    """管理單一語音頻道（Guild）的音樂播放狀態。"""

    QUEUE_PAGE_SIZE = 10

    def __init__(
        self,
        ctx: InteractionContext,
        search_service: Any | None = None,
    ) -> None:
        """初始化該伺服器的播放器狀態。

        Args:
            ctx (InteractionContext): 用於識別機器人、伺服器與文字頻道的上下文。
            search_service (Any | None, optional): 可供播放器面板「點歌」按鈕使用的搜尋服務。
                若未提供，面板仍可控制既有播放，但無法從 UI 直接新增歌曲。

        Returns:
            None.

        Notes:
            此處會立即為該伺服器建立一個背景播放迴圈任務。
        """
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.search_service = search_service
        self.queue = []
        self.history = []  # 用來存 previous
        self.next = asyncio.Event()
        self.current = None
        self.volume = 1.0
        self.previous_volume = None
        self.loop_mode = 0  # 0=off, 1=song, 2=queue

        self.start_timestamp = 0
        self.pause_timestamp = 0
        self.accumulated_pause = 0
        self.seek_offset = 0  # 用於傳遞給下一輪的跳轉指令
        self.current_song_start_offset = 0  # 記錄目前播放歌曲的起始偏移量，供進度條計算

        self.ytdl = create_player_ytdl()
        self.panel_message: discord.Message | None = None
        self.panel_view: discord.ui.View | None = None
        self.private_panel_message: discord.Message | None = None
        self.private_panel_view: discord.ui.View | None = None
        self.panel_page = 0
        self.panel_lock = asyncio.Lock()
        self.closed = False
        self.created_timestamp = time.time()
        self.has_started_playback = False
        self._force_advance = False
        self._force_add_history = True

        # 將背景任務存為實例變數，方便後續安全取消
        self.player_task = self.bot.loop.create_task(self.player_loop())
        self.player_task.add_done_callback(self._log_player_task_error)

    def _log_player_task_error(self, task: asyncio.Task) -> None:
        """記錄背景播放任務中未被處理的例外。"""
        if task.cancelled():
            return

        error = task.exception()
        if error:
            log.error(
                "音樂播放背景任務異常終止。",
                exc_info=(type(error), error, error.__traceback__),
            )

    def update_context(
        self,
        ctx: InteractionContext,
        search_service: Any | None = None,
    ) -> None:
        """更新播放器可使用的互動上下文資料。

        Args:
            ctx (InteractionContext): 最新一次觸發播放相關操作的 Discord 上下文。
            search_service (Any | None, optional): 可替換或補齊的音樂搜尋服務。

        Returns:
            None.

        Notes:
            已存在公開面板時不會搬移所在頻道，以避免點歌或切歌時產生新的播放器訊息。
        """
        if not self.panel_message:
            self.channel = ctx.channel
        if search_service is not None:
            self.search_service = search_service

    @property
    def is_active(self) -> bool:
        """判斷播放器目前是否仍有可控制的播放狀態。

        Returns:
            bool: 仍有歌曲、待播佇列或語音播放狀態時回傳 True。
        """
        if self.closed:
            return False

        vc = self.guild.voice_client if self.guild else None
        has_voice_activity = bool(
            vc and (vc.is_playing() or vc.is_paused())
        )
        return bool(self.current or self.queue or has_voice_activity)

    def get_loop_mode_label(self) -> str:
        """取得目前循環模式的人類可讀名稱。

        Returns:
            str: `關閉`、`單曲` 或 `佇列`。
        """
        if self.loop_mode == 0:
            return "關閉"
        return "單曲" if self.loop_mode == 1 else "佇列"

    def get_playback_status_label(self) -> str:
        """取得目前語音播放狀態的人類可讀名稱。

        Returns:
            str: 播放中、已暫停、準備中或已停止。
        """
        vc = self.guild.voice_client if self.guild else None
        if vc and vc.is_paused():
            return "已暫停"
        if vc and vc.is_playing():
            return "播放中"
        if self.current or self.queue:
            return "準備中"
        return "已停止"

    def get_queue_page_count(self) -> int:
        """計算待播佇列分頁總數。

        Returns:
            int: 分頁總數；佇列為空時仍回傳 1，方便 UI 顯示空頁。
        """
        if not self.queue:
            return 1
        return max(
            1,
            (len(self.queue) + self.QUEUE_PAGE_SIZE - 1) // self.QUEUE_PAGE_SIZE,
        )

    def clamp_queue_page(self, page: int) -> int:
        """將指定頁碼限制在目前佇列可顯示的範圍內。

        Args:
            page (int): 使用者目前要求顯示的 0-based 頁碼。

        Returns:
            int: 校正後的 0-based 頁碼。
        """
        return min(max(page, 0), self.get_queue_page_count() - 1)

    def build_panel_embed(
        self,
        *,
        page: int = 0,
        status_msg: str | None = None,
    ) -> discord.Embed:
        """依目前播放器狀態建立播放器面板 Embed。

        Args:
            page (int, optional): 待播歌單的 0-based 分頁頁碼。預設為 0。
            status_msg (str | None, optional): 顯示在頁尾的操作狀態訊息。

        Returns:
            discord.Embed: 可直接發送或編輯至 Discord 訊息的播放器面板。
        """
        page = self.clamp_queue_page(page)
        current = self.current
        title = "🎛️ 音樂播放器"
        embed_kwargs: dict[str, Any] = {
            "title": title,
            "color": (
                discord.Color.green()
                if self.is_active
                else discord.Color.dark_grey()
            ),
        }

        if current and current.get("webpage_url"):
            embed_kwargs["url"] = current["webpage_url"]

        embed = discord.Embed(**embed_kwargs)
        if current:
            embed.set_author(name=current.get("uploader", "未知"))
            embed.add_field(
                name="目前曲目",
                value=self._format_song_link(current),
                inline=False,
            )
            if current.get("thumbnail"):
                embed.set_thumbnail(url=current["thumbnail"])
        elif self.queue:
            embed.add_field(
                name="目前曲目",
                value="正在準備播放下一首歌曲。",
                inline=False,
            )
        else:
            embed.add_field(
                name="目前曲目",
                value="目前沒有播放中的歌曲。",
                inline=False,
            )

        duration = current.get("duration", 0) if current else 0
        current_time = self.get_current_time() if current else 0
        remaining_time = max(duration - current_time, 0) if duration else 0
        progress_bar = create_progress_bar(current_time, duration)

        embed.description = (
            f"狀態：`{self.get_playback_status_label()}`\n"
            f"進度：`{progress_bar}`\n"
            f"時間：`{format_time(current_time)} / {format_time(duration)}`"
            f"　剩餘：`{format_time(remaining_time)}`\n"
            f"音量：`{int(self.volume * 100)}%`　"
            f"循環：`{self.get_loop_mode_label()}`　"
            f"待播：`{len(self.queue)}`"
        )

        queue_value = self._format_queue_page(page)
        embed.add_field(
            name=f"待播歌單 第 {page + 1}/{self.get_queue_page_count()} 頁",
            value=queue_value,
            inline=False,
        )

        footer_text = status_msg or "使用下方按鈕控制播放與歌單。"
        embed.set_footer(text=f"操作狀態：{footer_text}")
        return embed

    def _format_song_link(self, song: dict[str, Any]) -> str:
        """將歌曲資訊轉為可放入 Embed 的短字串。

        Args:
            song (dict[str, Any]): 歌曲 metadata，至少應包含 title，可能包含 webpage_url 與 duration。

        Returns:
            str: 已截斷並帶有時長資訊的顯示字串。
        """
        title = self._truncate(song.get("title", "未知曲目"), 80)
        duration = format_time(song.get("duration", 0))
        url = song.get("webpage_url")
        if url:
            return f"[{title}]({url}) - `{duration}`"
        return f"{title} - `{duration}`"

    def _format_queue_page(self, page: int) -> str:
        """格式化指定頁面的待播歌曲清單。

        Args:
            page (int): 0-based 分頁頁碼。

        Returns:
            str: 最多十首歌曲的編號、標題與時長；若佇列為空則回傳空佇列提示。
        """
        if not self.queue:
            return "佇列目前是空的。"

        start = page * self.QUEUE_PAGE_SIZE
        end = start + self.QUEUE_PAGE_SIZE
        lines = []
        for index, song in enumerate(self.queue[start:end], start=start + 1):
            title = self._truncate(song.get("title", "未知曲目"), 70)
            duration = format_time(song.get("duration", 0))
            lines.append(f"`{index:02d}.` {title} - `{duration}`")

        return "\n".join(lines)

    def _truncate(self, value: str, limit: int) -> str:
        """將過長字串截斷為 Discord UI 易讀的長度。

        Args:
            value (str): 原始字串。
            limit (int): 最大字元數。

        Returns:
            str: 未超過指定長度的字串。
        """
        if len(value) <= limit:
            return value
        return value[: limit - 3] + "..."

    async def refresh_public_panel(self, status_msg: str | None = None) -> None:
        """建立或原地更新公開播放器面板。

        Args:
            status_msg (str | None, optional): 要顯示在面板頁尾的操作狀態。

        Returns:
            None.

        Notes:
            若面板訊息仍存在，永遠優先編輯原訊息；只有原訊息被刪除或尚未建立時才會重新發送。
            若目前存在私人面板，會先移除私人面板，確保同一時間只有一個播放器介面可操作。
        """
        if self.closed or not self.is_active:
            return

        async with self.panel_lock:
            await self._retire_private_panel_unlocked()

            self.panel_page = self.clamp_queue_page(self.panel_page)
            embed = self.build_panel_embed(page=self.panel_page, status_msg=status_msg)
            view = PlayerControls(self, page=self.panel_page)

            if self.panel_message:
                previous_view = self.panel_view
                try:
                    await self.panel_message.edit(embed=embed, view=view)
                    self._release_panel_view(previous_view)
                    self.panel_view = view
                    return
                except discord.NotFound:
                    self._release_panel_view(previous_view)
                    self.panel_message = None
                    self.panel_view = None
                except discord.HTTPException as e:
                    self._release_panel_view(view)
                    log.warning(f"更新播放器面板失敗: {e}")
                    return

            if not self.channel:
                self._release_panel_view(view)
                return

            self.panel_view = view
            try:
                self.panel_message = await self.channel.send(embed=embed, view=view)
            except discord.HTTPException as e:
                self.panel_view = None
                self._release_panel_view(view)
                log.warning(f"建立播放器面板失敗: {e}")

    async def show_private_panel(
        self,
        ctx: InteractionContext,
        *,
        owner_id: int,
    ) -> discord.Message | None:
        """建立僅指定使用者可操作的私人播放器面板。

        Args:
            ctx (InteractionContext): 用於發送私人面板的互動上下文。
            owner_id (int): 允許操作此私人面板的 Discord 使用者 ID。

        Returns:
            discord.Message | None: 成功建立時回傳面板訊息；播放器已停止時回傳 None。

        Notes:
            建立私人面板前會先移除目前的公開或私人面板，避免同時存在兩個可操作的播放器介面。
        """
        if self.closed or not self.is_active:
            return None

        async with self.panel_lock:
            if self.closed or not self.is_active:
                return None

            await self._retire_public_panel_unlocked()
            await self._retire_private_panel_unlocked()

            self.panel_page = self.clamp_queue_page(self.panel_page)
            embed = self.build_panel_embed(
                page=self.panel_page,
                status_msg="已叫出私人播放器面板。",
            )
            view = PlayerControls(
                self,
                owner_id=owner_id,
                page=self.panel_page,
                timeout=None,
            )

            self.private_panel_view = view
            try:
                message = await ctx.send(embed=embed, view=view)
            except discord.HTTPException:
                self.private_panel_view = None
                self._release_panel_view(view)
                raise

            self.private_panel_message = message
            return message

    async def hide_public_panel(self) -> None:
        """讓公開播放器面板不可見或不可控制。

        Returns:
            None.

        Notes:
            系統會優先刪除訊息以達到不可見；若 Discord 權限或 API 狀態不允許刪除，
            則退回清空訊息內容與控制元件，確保使用者不能再操作舊面板。
        """
        async with self.panel_lock:
            await self._retire_public_panel_unlocked()

    async def hide_all_panels(self) -> None:
        """移除所有播放器控制面板並釋放 View 引用。"""
        async with self.panel_lock:
            await self._retire_public_panel_unlocked()
            await self._retire_private_panel_unlocked()

    async def _retire_public_panel_unlocked(self) -> None:
        """在已持有 panel_lock 時移除公開面板。"""
        message = self.panel_message
        view = self.panel_view
        if not message and not view:
            return

        self.panel_message = None
        self.panel_view = None
        await self._retire_panel_message(message, view)

    async def _retire_private_panel_unlocked(self) -> None:
        """在已持有 panel_lock 時移除私人面板。"""
        message = self.private_panel_message
        view = self.private_panel_view
        if not message and not view:
            return

        self.private_panel_message = None
        self.private_panel_view = None
        await self._retire_panel_message(message, view)

    def _release_panel_view(self, view: discord.ui.View | None) -> None:
        """停止舊 View，讓 Discord.py 不再派發舊按鈕互動。"""
        if not view:
            return

        try:
            view.stop()
        except Exception:
            log.debug("停止播放器面板 View 時發生非預期錯誤。", exc_info=True)

    async def _retire_panel_message(
        self,
        message: discord.Message | None,
        view: discord.ui.View | None,
    ) -> None:
        """刪除或清空舊面板訊息，並停止 View 釋放引用。"""
        self._release_panel_view(view)
        if not message:
            gc.collect()
            return

        try:
            await message.delete()
            gc.collect()
            return
        except discord.NotFound:
            gc.collect()
            return
        except discord.HTTPException:
            pass

        try:
            await message.edit(content="\u200b", embed=None, view=None)
        except discord.HTTPException:
            pass
        finally:
            gc.collect()

    def request_next_track(self) -> bool:
        """要求播放器跳到下一首歌曲。

        Returns:
            bool: 成功送出切歌請求時回傳 True；目前沒有可停止的音訊時回傳 False。

        Notes:
            此方法會暫時覆蓋單曲循環，確保使用者按下下一首或跳過時不會重播同一首。
        """
        vc = self.guild.voice_client if self.guild else None
        if not vc or not (vc.is_playing() or vc.is_paused()):
            return False

        self._force_advance = True
        self._force_add_history = True
        vc.stop()
        return True

    def request_previous_track(self) -> bool:
        """要求播放器回到上一首歌曲。

        Returns:
            bool: 成功送出上一首請求時回傳 True；沒有歷史紀錄或無法停止音訊時回傳 False。
        """
        vc = self.guild.voice_client if self.guild else None
        if not vc or not (vc.is_playing() or vc.is_paused()):
            return False
        if not self.history:
            return False

        previous_song = self.history.pop()
        if self.current:
            self.queue.insert(0, self.current)
        self.queue.insert(0, previous_song)
        self._force_advance = True
        self._force_add_history = True
        vc.stop()
        return True

    def request_seek(self, seconds: int) -> bool:
        """要求播放器從指定秒數重新播放目前歌曲。

        Args:
            seconds (int): 欲跳轉的目標秒數，必須大於或等於 0。

        Returns:
            bool: 成功送出跳轉請求時回傳 True；目前無法跳轉時回傳 False。

        Notes:
            Discord VoiceClient 不支援熱跳轉，因此此方法會把目前歌曲放回佇列頂端，
            再透過 FFmpeg `-ss` 參數於下一輪播放時從指定時間開始。
        """
        vc = self.guild.voice_client if self.guild else None
        if seconds < 0 or not self.current or not vc:
            return False
        if not (vc.is_playing() or vc.is_paused()):
            return False

        self.seek_offset = seconds
        self.queue.insert(0, self.current)
        self._force_advance = True
        self._force_add_history = False
        vc.stop()
        return True

    async def cleanup(self) -> None:
        """清理播放器資源，優雅關閉 FFmpeg 與背景任務。"""
        await self.shutdown()

    async def shutdown(
        self,
        *,
        disconnect: bool = True,
        remove_from_registry: bool = True,
    ) -> None:
        """停止播放器並釋放該 Guild 的音樂資源。

        Args:
            disconnect (bool, optional): 是否中斷語音連線。預設為 True。
            remove_from_registry (bool, optional): 是否從全域播放器快取移除。預設為 True。

        Returns:
            None.

        Notes:
            當播放自然結束或使用者執行停止指令時呼叫此方法，面板會被刪除或停用，
            佇列與歷史資料會清空，最後觸發 Python 垃圾回收釋放 yt-dlp/FFmpeg 相關引用。
        """
        if self.closed:
            return

        self.closed = True
        self.queue.clear()
        self.history.clear()
        self.current = None
        self.loop_mode = 0
        self.seek_offset = 0
        self.current_song_start_offset = 0
        self.next.set()

        # 若有動態歌詞任務，予以安全取消
        if hasattr(self, "lyrics_task") and self.lyrics_task:
            self.lyrics_task.cancel()

        await self.hide_all_panels()

        # 安全停止音樂與斷開連線，這會讓 discord.py 正常發送 SIGTERM 給 FFmpeg
        if self.guild.voice_client:
            if (
                self.guild.voice_client.is_playing()
                or self.guild.voice_client.is_paused()
            ):
                self.guild.voice_client.stop()
            if disconnect:
                await self.guild.voice_client.disconnect(force=False)

        # 取消主播放迴圈任務
        current_task = asyncio.current_task()
        if (
            self.player_task
            and not self.player_task.done()
            and self.player_task is not current_task
        ):
            self.player_task.cancel()

        if remove_from_registry and self.guild:
            players.pop(self.guild.id, None)

        self.search_service = None
        self.ytdl = None
        gc.collect()

    def pause_time(self) -> None:
        """記錄播放暫停時的時間戳記。

        Args:
            無。

        Returns:
            None.

        Notes:
            此時間戳記用於確保播放進度條在暫停與恢復時依然精準。
        """
        self.pause_timestamp = time.time()

    def resume_time(self) -> None:
        """播放恢復後，計算並累計暫停期間的時間差。

        Args:
            無。

        Returns:
            None.

        Notes:
            若播放器並未處於暫停狀態，則不會進行任何狀態變更。
        """
        if self.pause_timestamp > 0:
            self.accumulated_pause += time.time() - self.pause_timestamp
            self.pause_timestamp = 0

    def get_current_time(self) -> float:
        """計算目前的播放位置（秒數）。

        Args:
            無。

        Returns:
            float: 目前的播放進度，包含跳轉 (seek) 的偏移量。

        Notes:
            若播放尚未開始，則回傳 0。
        """
        if self.start_timestamp == 0:
            return 0
        if self.pause_timestamp > 0:
            return (
                self.pause_timestamp
                - self.start_timestamp
                - self.accumulated_pause
                + self.current_song_start_offset
            )
        return (
            time.time()
            - self.start_timestamp
            - self.accumulated_pause
            + self.current_song_start_offset
        )

    async def add_to_queue(
        self,
        song_info: dict,
        ctx: InteractionContext,
        insert_at_front: bool = False,
        announce: bool = True,
    ) -> None:
        """將歌曲資訊字典加入播放佇列。

        Args:
            song_info (dict): 包含標題、URL 及其他 metadata 的佇列項目。
            ctx (InteractionContext): 用於發送通知訊息的內容上下文。
            insert_at_front (bool): 是否插入至佇列最前端。
            announce (bool): 是否發送 Discord 加入佇列的通知訊息。

        Returns:
            None.

        Notes:
            插入至最前端的操作為靜默執行，因為呼叫者通常會自行處理回覆訊息。
        """
        self.update_context(ctx)

        if insert_at_front:
            self.queue.insert(0, song_info)
        else:
            self.queue.append(song_info)
            log.info(
                f"已加入播放佇列: {song_info.get('title', '未知曲目')} "
                f"(queue={len(self.queue)})"
            )
            if announce and (len(self.queue) > 1 or ctx.voice_client.is_playing()):
                await ctx.send(
                    f"✅ 已將 **{song_info['title']}** 加入播放佇列！ (目前排在第 {len(self.queue)} 首)"
                )

        await self.refresh_public_panel(
            f"已加入：{self._truncate(song_info.get('title', '未知曲目'), 40)}"
        )

    async def player_loop(self) -> None:
        """伺服器的音樂播放主迴圈。

        Args:
            無。

        Returns:
            None.

        Notes:
            此迴圈負責自動從佇列抓取歌曲、執行 YouTube 網址解析 (JIT)、
            應用跳轉偏移量並自動處理播放完畢後的循環模式。
        """
        await self.bot.wait_until_ready()
        try:
            while not self.bot.is_closed():
                self.next.clear()

                if not self.current and len(self.queue) == 0:
                    if self.has_started_playback:
                        await self.shutdown()
                        break

                    if time.time() - self.created_timestamp > 60:
                        await self.shutdown(disconnect=False)
                        break

                    await asyncio.sleep(1)
                    continue

                # 如果沒有設定 current，從 queue 取歌
                if not self.current and len(self.queue) > 0:
                    self.current = self.queue.pop(0)

                # 如果網址不是 videoplayback 串流，代表它是從播放清單載入的永久網址，需即時解析
                if "videoplayback" not in self.current["url"]:
                    try:
                        loop = asyncio.get_event_loop()
                        # 即時抓取最新鮮的串流網址
                        data = await loop.run_in_executor(
                            None,
                            lambda: self.ytdl.extract_info(
                                self.current["url"], download=False
                            ),
                        )

                        # 更新成可以給 FFmpeg 播放的直連網址
                        self.current["url"] = data["url"]

                        # 若清單資料缺失則補齊資訊
                        self.current["duration"] = data.get(
                            "duration"
                        ) or self.current.get("duration", 0)
                        self.current["uploader"] = data.get(
                            "uploader"
                        ) or self.current.get("uploader", "未知")
                        if data.get("thumbnails"):
                            self.current["thumbnail"] = data["thumbnails"][0]["url"]

                    except Exception as e:
                        log.exception(f"即時解析歌曲失敗: {e}")
                        self.current = None
                        if not self.queue:
                            await self.shutdown()
                            break
                        self.bot.loop.call_soon_threadsafe(self.next.set)
                        continue

                if not self.guild.voice_client:
                    log.warning("播放前語音連線已不存在，略過目前歌曲。")
                    self.current = None
                    if not self.queue:
                        await self.shutdown(disconnect=False)
                        break
                    continue

                # 組裝 FFmpeg 選項 (必須將 -ss 放在 -reconnect 前面以提升跳轉速度)
                before_opts = ""
                if self.seek_offset > 0:
                    before_opts += f"-ss {int(self.seek_offset)} "

                before_opts += (
                    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                )
                ffmpeg_options = {"options": "-vn", "before_options": before_opts}

                try:
                    audio_source = discord.FFmpegPCMAudio(
                        self.current["url"], **ffmpeg_options
                    )
                    volume_source = discord.PCMVolumeTransformer(
                        audio_source, volume=self.volume
                    )
                except Exception as e:
                    log.exception(f"建立 FFmpeg 音源失敗: {e}")
                    if self.channel:
                        await self.channel.send(
                            f"⚠️ 建立音訊來源失敗，已略過：**{self.current.get('title', '未知曲目')}**"
                        )
                    self.current = None
                    if not self.queue:
                        await self.shutdown()
                        break
                    continue

                self.start_timestamp = time.time()
                self.accumulated_pause = 0
                self.pause_timestamp = 0

                # 在播放前保存目前的跳轉偏移量，然後將實體偏移歸零
                current_seek = self.seek_offset
                self.current_song_start_offset = current_seek
                self.seek_offset = 0

                def after_play(error: Exception) -> None:
                    """discord.py 播放完畢後的 Callback 函式。

                    Args:
                        error (Exception): 若播放中發生錯誤，此參數會包含錯誤資訊。

                    Returns:
                        None.

                    Notes:
                        此回呼在主執行緒外觸發，故透過 `call_soon_threadsafe` 來喚醒非同步迴圈。
                    """
                    finished_song = self.current
                    if error:
                        log.error(
                            "播放期間發生錯誤。",
                            exc_info=(type(error), error, error.__traceback__),
                        )

                    force_advance = self._force_advance
                    force_add_history = self._force_add_history
                    self._force_advance = False
                    self._force_add_history = True

                    if force_advance or self.loop_mode == 0:  # 關閉循環或手動切歌
                        if finished_song and force_add_history:
                            self.history.append(finished_song)
                            if len(self.history) > 20:
                                self.history.pop(0)
                        self.current = None
                    elif self.loop_mode == 1:  # 單曲循環
                        pass
                    elif self.loop_mode == 2:  # 佇列循環
                        if finished_song:
                            self.queue.append(finished_song)
                            self.history.append(finished_song)
                        self.current = None

                    self.bot.loop.call_soon_threadsafe(self.next.set)

                # 若非跳轉指令則更新固定播放面板；切歌不會建立新的播放器訊息。
                if current_seek == 0:
                    await self.refresh_public_panel(
                        f"正在播放：{self._truncate(self.current.get('title', '未知曲目'), 40)}"
                    )

                try:
                    self.guild.voice_client.play(volume_source, after=after_play)
                except Exception as e:
                    log.exception(f"啟動語音播放失敗: {e}")
                    if self.channel:
                        await self.channel.send(
                            f"⚠️ 啟動播放失敗，已略過：**{self.current.get('title', '未知曲目')}**"
                        )
                    self.current = None
                    if not self.queue:
                        await self.shutdown()
                        break
                    continue

                self.has_started_playback = True
                log.info(f"開始播放: {self.current.get('title', '未知曲目')}")
                await self.next.wait()

        except asyncio.CancelledError:
            # 捕捉任務取消例外，避免印出錯誤堆疊，確保安靜退出
            pass


players: dict[int, MusicPlayer] = {}


def get_existing_player(ctx: InteractionContext) -> MusicPlayer | None:
    """取得已存在且尚未關閉的伺服器播放器。

    Args:
        ctx (InteractionContext): 用於識別伺服器的內容上下文。

    Returns:
        MusicPlayer | None: 找得到活躍播放器時回傳該實例，否則回傳 None。
    """
    if not ctx.guild:
        return None

    player = players.get(ctx.guild.id)
    if not player or player.closed:
        return None
    return player


def get_player(
    ctx: InteractionContext,
    search_service: Any | None = None,
) -> MusicPlayer:
    """取得該伺服器的專屬播放器實例。

    Args:
        ctx (InteractionContext): 用於識別伺服器的內容上下文。
        search_service (Any | None, optional): 可供播放器 UI 點歌功能使用的搜尋服務。

    Returns:
        MusicPlayer: 該伺服器活躍的播放器實例。

    Notes:
        若機器人被強制斷線但佇列內仍有歌曲，則會自動重建播放器實例。
    """
    if not ctx.guild:
        raise RuntimeError("音樂播放器只能在 Discord 伺服器中建立。")

    player = players.get(ctx.guild.id)
    if not player or player.closed:
        player = MusicPlayer(ctx, search_service=search_service)
        players[ctx.guild.id] = player
        return player

    if ctx.voice_client is None and len(player.queue) > 0:
        awaitable_cleanup = player.shutdown(
            disconnect=False,
            remove_from_registry=False,
        )
        ctx.bot.loop.create_task(awaitable_cleanup)
        player = MusicPlayer(ctx, search_service=search_service)
        players[ctx.guild.id] = player
        return player

    player.update_context(ctx, search_service=search_service)
    return player
