# music/player.py - 管理播放佇列、語音播放、循環模式與跳轉邏輯
import asyncio
import time

import discord

from music.services import create_player_ytdl
from music.ui import PlayerControls
from music.utils import format_time


class MusicPlayer:
    """管理單一語音頻道（Guild）的音樂播放狀態。"""

    def __init__(self, ctx: discord.ext.commands.Context) -> None:
        """初始化該伺服器的播放器狀態。

        Args:
            ctx (discord.ext.commands.Context): 用於識別機器人、伺服器與文字頻道的上下文。

        Returns:
            None.

        Notes:
            此處會立即為該伺服器建立一個背景播放迴圈任務。
        """
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
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
        self.current_song_start_offset = 0  # 記錄當前播放歌曲的起始偏移量，供進度條計算

        self.ytdl = create_player_ytdl()

        self.bot.loop.create_task(self.player_loop())

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
        ctx: discord.ext.commands.Context,
        insert_at_front: bool = False,
        announce: bool = True,
    ) -> None:
        """將歌曲資訊字典加入播放佇列。

        Args:
            song_info (dict): 包含標題、URL 及其他 metadata 的佇列項目。
            ctx (discord.ext.commands.Context): 用於發送通知訊息的內容上下文。
            insert_at_front (bool): 是否插入至佇列最前端。
            announce (bool): 是否發送 Discord 加入佇列的通知訊息。

        Returns:
            None.

        Notes:
            插入至最前端的操作為靜默執行，因為呼叫者通常會自行處理回覆訊息。
        """
        if insert_at_front:
            self.queue.insert(0, song_info)
        else:
            self.queue.append(song_info)
            if announce and (len(self.queue) > 1 or ctx.voice_client.is_playing()):
                await ctx.send(
                    f"✅ 已將 **{song_info['title']}** 加入播放佇列！ (目前排在第 {len(self.queue)} 首)"
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
        while not self.bot.is_closed():
            self.next.clear()

            if not self.current and len(self.queue) == 0:
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
                    self.current["duration"] = data.get("duration") or self.current.get(
                        "duration", 0
                    )
                    self.current["uploader"] = data.get("uploader") or self.current.get(
                        "uploader", "未知"
                    )
                    if data.get("thumbnails"):
                        self.current["thumbnail"] = data["thumbnails"][0]["url"]

                except Exception as e:
                    print(f"即時解析歌曲失敗: {e}")
                    self.current = None
                    self.bot.loop.call_soon_threadsafe(self.next.set)
                    continue

            # 組裝 FFmpeg 選項 (必須將 -ss 放在 -reconnect 前面以提升跳轉速度)
            before_opts = ""
            if self.seek_offset > 0:
                before_opts += f"-ss {int(self.seek_offset)} "

            before_opts += "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            ffmpeg_options = {"options": "-vn", "before_options": before_opts}

            audio_source = discord.FFmpegPCMAudio(self.current["url"], **ffmpeg_options)
            volume_source = discord.PCMVolumeTransformer(
                audio_source, volume=self.volume
            )

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
                    print(f"播放錯誤: {error}")

                if self.loop_mode == 0:  # 關閉循環
                    if finished_song:
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

            # 若非跳轉指令則發送播放面板
            if current_seek == 0:
                embed_kwargs = {
                    "title": f"🎶 正在播放：{self.current['title']}",
                    "color": discord.Color.green(),
                }
                if self.current.get("webpage_url"):
                    embed_kwargs["url"] = self.current["webpage_url"]
                embed = discord.Embed(**embed_kwargs)
                embed.set_author(name=self.current.get("uploader", "未知"))
                embed.description = (
                    f"⏱️ 時長：{format_time(self.current.get('duration'))}"
                )
                if self.current.get("thumbnail"):
                    embed.set_thumbnail(url=self.current["thumbnail"])
                await self.channel.send(embed=embed, view=PlayerControls(self))

            self.guild.voice_client.play(volume_source, after=after_play)
            await self.next.wait()


players = {}


def get_player(ctx: discord.ext.commands.Context) -> MusicPlayer:
    """取得該伺服器的專屬播放器實例。

    Args:
        ctx (discord.ext.commands.Context): 用於識別伺服器的內容上下文。

    Returns:
        MusicPlayer: 該伺服器活躍的播放器實例。

    Notes:
        若機器人被強制斷線但佇列內仍有歌曲，則會自動重建播放器實例。
    """
    if ctx.guild.id not in players:
        players[ctx.guild.id] = MusicPlayer(ctx)
    if ctx.voice_client is None and len(players[ctx.guild.id].queue) > 0:
        players[ctx.guild.id] = MusicPlayer(ctx)
    return players[ctx.guild.id]
