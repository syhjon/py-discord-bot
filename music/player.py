# player.py - 音樂播放器核心邏輯
import asyncio
import time

import discord

from music.services import create_player_ytdl
from music.ui import PlayerControls
from music.utils import format_time


class MusicPlayer:
    def __init__(self, ctx):
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
        self.current_song_start_offset = (
            0  # 👈 新增：用於記錄當前播放歌曲的起始偏移量，供進度條計算
        )

        self.ytdl = create_player_ytdl()

        self.bot.loop.create_task(self.player_loop())

    def pause_time(self):
        self.pause_timestamp = time.time()

    def resume_time(self):
        if self.pause_timestamp > 0:
            self.accumulated_pause += time.time() - self.pause_timestamp
            self.pause_timestamp = 0

    def get_current_time(self):
        if self.start_timestamp == 0:
            return 0
        if self.pause_timestamp > 0:
            return (
                self.pause_timestamp
                - self.start_timestamp
                - self.accumulated_pause
                + self.current_song_start_offset  # 👈 改用記錄這首歌實際起始點的變數
            )
        return (
            time.time()
            - self.start_timestamp
            - self.accumulated_pause
            + self.current_song_start_offset  # 👈 改用記錄這首歌實際起始點的變數
        )

    async def add_to_queue(self, song_info, ctx, insert_at_front=False, announce=True):
        if insert_at_front:
            self.queue.insert(0, song_info)
        else:
            self.queue.append(song_info)
            if announce and (len(self.queue) > 1 or ctx.voice_client.is_playing()):
                await ctx.send(
                    f"✅ 已將 **{song_info['title']}** 加入播放佇列！ (目前排在第 {len(self.queue)} 首)"
                )

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()

            if not self.current and len(self.queue) == 0:
                await asyncio.sleep(1)
                continue

            # 如果沒有設定 current，從 queue 取歌
            if not self.current and len(self.queue) > 0:
                self.current = self.queue.pop(0)

            # 如果網址不是 videoplayback 串流，代表它是從播放清單載入的永久網址，我們必須即時把它轉成串流
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

                    # 如果原本清單裡沒有時長或封面，順便在這裡補齊
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
                    # 解析失敗就跳過這首歌，播下一首
                    self.current = None
                    self.bot.loop.call_soon_threadsafe(self.next.set)
                    continue

            # 組裝 FFmpeg options (包含跳轉邏輯)
            # 👈 關鍵修正 1：FFmpeg 參數順序，-ss 必須放在 reconnect 的前面！
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

            # 👈 關鍵修正 2：在送出播放指令前，保存這次跳轉的秒數給進度條，然後將跳轉指令歸零
            current_seek = self.seek_offset
            self.current_song_start_offset = current_seek
            self.seek_offset = 0

            def after_play(error):
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
                    pass  # current 保持不變
                elif self.loop_mode == 2:  # 佇列循環
                    if finished_song:
                        self.queue.append(finished_song)
                        self.history.append(finished_song)
                    self.current = None

                # ⚠️ 這裡已經移除了 self.seek_offset = 0，因為我們移到上面去了
                self.bot.loop.call_soon_threadsafe(self.next.set)

            # 只在非跳轉 (seek) 時發送面板。注意這裡用 current_seek 判斷
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


def get_player(ctx):
    if ctx.guild.id not in players:
        players[ctx.guild.id] = MusicPlayer(ctx)
    # 如果機器人被踢出頻道，重置 player
    if ctx.voice_client is None and len(players[ctx.guild.id].queue) > 0:
        players[ctx.guild.id] = MusicPlayer(ctx)
    return players[ctx.guild.id]
