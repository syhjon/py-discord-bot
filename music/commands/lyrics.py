# music/commands/lyrics.py - 提供歌詞搜尋與顯示功能的指令 Mixin
import asyncio
import json
import os
import re
import urllib.parse
import time
from typing import Any, Dict, List, Tuple

import aiohttp
import discord
from discord.ext import commands

from music.player import get_player


class LyricsCommandMixin:
    """提供歌詞查詢指令與動態歌詞顯示的 Mixin 類別。"""

    @commands.command(name="lyrics", aliases=["ly"], help="搜尋目前播放歌曲的歌詞")
    async def lyrics_command(self, ctx: commands.Context) -> None:
        """獲取當前播放歌曲的歌詞。具備本地快取、AI 解析與自動降級搜尋功能。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。

        Returns:
            None.
        """
        player = get_player(ctx)

        if not player or not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        # 延遲初始化：確保本地端存放歌詞的目錄存在
        lyrics_dir = os.path.join(os.getcwd(), "lyrics")
        os.makedirs(lyrics_dir, exist_ok=True)

        # 1. 取得當前網址，並萃取 YouTube 影片 ID 作為檔名
        raw_url = player.current.get("webpage_url", player.current.get("url", ""))
        match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", raw_url)
        video_id = match.group(1) if match else None

        if not video_id:
            return await ctx.send(
                "❌ 無法解析當前歌曲的 YouTube ID，無法建立歌詞快取。"
            )

        cache_path = os.path.join(lyrics_dir, f"{video_id}.json")

        # 2. 檢查是否有本地快取
        if os.path.exists(cache_path):
            msg = await ctx.send("📂 找到本地歌詞快取，正在載入中...")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                await self._process_and_display_lyrics(
                    ctx, msg, player, cached_data, raw_url
                )
                return
            except json.JSONDecodeError:
                await msg.edit(content="⚠️ 快取檔案損毀，重新向網路搜尋...")
        else:
            msg = await ctx.send("🔍 正在準備搜尋歌詞...")

        raw_title = player.current.get("title", "")
        uploader = player.current.get("uploader", "")

        # 用於儲存最終從 API 取得的資料
        fetched_data = None

        # ==========================================
        # 階段一：嘗試 AI 智慧解析與精確搜尋
        # ==========================================
        if hasattr(self, "gemini") and self.gemini.is_configured:
            await msg.edit(content=f"🤖 正在請 AI 解析歌曲資訊：**{raw_title}** ...")
            try:
                prompt = (
                    "【系統指令：請忽略原本的友善對話設定，嚴格遵守以下輸出格式】\n"
                    "請分析以下 YouTube 影片標題與上傳者，萃取出準確的「歌曲名稱 (Track Name)」與「歌手名稱 (Artist Name)」。\n"
                    f"標題：{raw_title}\n"
                    f"上傳者：{uploader}\n"
                    "請務必「只」回傳一個 JSON 格式的陣列（Array），第 0 項是歌名，第 1 項是歌手。\n"
                    '範例輸出：["Say My Name", "Odesza"]\n'
                    '如果完全無法辨識，請回傳 ["", ""]。絕不能有任何其他說明文字或 Markdown 標記。'
                )
                ai_response = await self.gemini.generate_answer(prompt)

                track_name, artist_name = "", ""
                match_json = re.search(r"\[(.*?)\]", ai_response, re.DOTALL)
                if match_json:
                    parsed_json = json.loads(match_json.group(0))
                    if isinstance(parsed_json, list) and len(parsed_json) >= 2:
                        track_name = str(parsed_json[0]).strip()
                        artist_name = str(parsed_json[1]).strip()

                # 如果成功解析出歌名與歌手，嘗試使用精確 API
                if track_name and artist_name:
                    await msg.edit(
                        content=f"🔍 向資料庫請求精準匹配：**{track_name}** - **{artist_name}** ..."
                    )
                    encoded_track = urllib.parse.quote(track_name)
                    encoded_artist = urllib.parse.quote(artist_name)
                    url_get = f"https://lrclib.net/api/get?track_name={encoded_track}&artist_name={encoded_artist}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url_get, timeout=10) as response:
                            if response.status == 200:
                                fetched_data = await response.json()
            except Exception as e:
                print(f"Gemini API Error (503/Timeout): {e}")
                await msg.edit(
                    content="⚠️ AI 服務目前滿載或無回應，自動啟動降級搜尋方案..."
                )
                await asyncio.sleep(1.5)

        # ==========================================
        # 階段二：降級方案 (傳統字串清理 + 模糊搜尋)
        # ==========================================
        if not fetched_data:
            clean_title = re.sub(
                r"\|.*|\(.*\)|\[.*\]|Soundtrack|Official|MV|官方|錄影|Lyric|Video",
                "",
                raw_title,
                flags=re.IGNORECASE,
            ).strip()

            await msg.edit(
                content=f"🔍 正在使用傳統關鍵字模糊搜尋：**{clean_title}** ..."
            )
            encoded_query = urllib.parse.quote(clean_title)
            url_search = f"https://lrclib.net/api/search?q={encoded_query}"

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url_search, timeout=10) as response:
                        if response.status == 200:
                            data_list = await response.json()
                            if (
                                data_list
                                and isinstance(data_list, list)
                                and len(data_list) > 0
                            ):
                                fetched_data = data_list[0]
                        else:
                            return await msg.edit(
                                content=f"⚠️ LRCLIB API 發生異常 (狀態碼: {response.status})"
                            )
            except Exception as e:
                print(f"LRCLIB Search Error: {e}")
                return await msg.edit(content="⚠️ 連線至歌詞庫時發生網路錯誤。")

        # ==========================================
        # 階段三：儲存快取與顯示
        # ==========================================
        if fetched_data:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(fetched_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Cache Write Error: {e}")

            await self._process_and_display_lyrics(
                ctx, msg, player, fetched_data, raw_url
            )
        else:
            await msg.edit(content="❌ 資料庫中找不到這首歌的相關歌詞。")

    async def _process_and_display_lyrics(
        self,
        ctx: commands.Context,
        msg: discord.Message,
        player: Any,
        data: Dict[str, Any],
        raw_url: str,
    ) -> None:
        """決定採用動態歌詞或靜態全文本顯示。"""
        synced_lyrics = data.get("syncedLyrics")
        plain_lyrics = data.get("plainLyrics")
        title = data.get("trackName", "未知曲目")
        artist = data.get("artistName", "未知歌手")

        if synced_lyrics:
            parsed_lyrics = self._parse_synced_lyrics(synced_lyrics)
            if parsed_lyrics:
                # 確保舊的任務被確實取消
                if hasattr(player, "lyrics_task") and player.lyrics_task:
                    player.lyrics_task.cancel()

                # 指派新的任務給播放器
                player.lyrics_task = asyncio.create_task(
                    self._sync_lyrics_task(
                        ctx, msg, player, parsed_lyrics, raw_url, title, artist
                    )
                )
                return

        if plain_lyrics:
            if len(plain_lyrics) > 1850:
                plain_lyrics = plain_lyrics[:1850] + "\n\n...(歌詞過長，已截斷)"
            await msg.edit(
                content=f"📜 **{title} - {artist}**\n```text\n{plain_lyrics}\n```"
            )
        else:
            await msg.edit(content="❌ 雖然找到了該歌曲，但資料庫內無可用的歌詞文本。")

    def _parse_synced_lyrics(self, raw_synced: str) -> List[Tuple[float, str]]:
        """將 `[mm:ss.xx] 歌詞` 解析為 (秒數, 歌詞字串) 的陣列。"""
        lines = raw_synced.split("\n")
        parsed = []
        for line in lines:
            match = re.match(r"\[(\d{2,}):(\d{2}(?:\.\d+)?)\]\s*(.*)", line.strip())
            if match:
                m, s, text = match.groups()
                time_sec = int(m) * 60 + float(s)
                parsed.append((time_sec, text or "🎵"))
        return parsed

    async def _sync_lyrics_task(
        self,
        ctx: commands.Context,
        msg: discord.Message,
        player: Any,
        parsed_lyrics: List[Tuple[float, str]],
        target_url: str,
        title: str,
        artist: str,
    ) -> None:
        """背景任務：根據當前播放時間，動態更新 Embed 顯示的歌詞。

        具備嚴格的生命週期監控，若被插播、跳過或停止，將會立即自毀。
        """
        current_index = -2
        last_edit_time = 0.0

        embed = discord.Embed(
            title=f"🎤 動態歌詞: {title} - {artist}", color=discord.Color.blue()
        )
        await msg.edit(content=None, embed=embed)

        try:
            while player.current:
                # 1. 檢查是否被切歌或插播 (URL 改變)，若是則立刻結束任務
                current_url = player.current.get(
                    "webpage_url", player.current.get("url", "")
                )
                if current_url != target_url:
                    break

                vc = ctx.voice_client

                # 2. 檢查是否從語音頻道斷線
                if not vc or not vc.is_connected():
                    break

                # 3. 檢查播放狀態 (防範殭屍程序)
                if not vc.is_playing():
                    if vc.is_paused():
                        # 若處於暫停狀態，進入極低耗能休眠，不執行歌詞進度計算
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        # 既沒在播也沒在暫停，代表已經被 stop() 砍掉，立刻結束任務
                        break

                current_time = player.get_current_time()

                # 計算目前應該顯示的歌詞句
                target_index = -1
                for i, (t, _) in enumerate(parsed_lyrics):
                    if current_time >= t:
                        target_index = i
                    else:
                        break

                # 更新 Discord 訊息 (限制最高刷新頻率為 1.5 秒以符合 API Rate Limit)
                if target_index != current_index:
                    now = time.time()
                    if now - last_edit_time >= 1.5:
                        current_index = target_index

                        desc = ""
                        if target_index == -1:
                            desc += "🎵 *(前奏中...)*\n\n"
                            if parsed_lyrics:
                                desc += f"即將演唱：*{parsed_lyrics[0][1]}*"
                        else:
                            prev_line = (
                                parsed_lyrics[target_index - 1][1]
                                if target_index > 0
                                else ""
                            )
                            curr_line = parsed_lyrics[target_index][1]
                            next_line = (
                                parsed_lyrics[target_index + 1][1]
                                if target_index < len(parsed_lyrics) - 1
                                else ""
                            )

                            if prev_line:
                                desc += f"*{prev_line}*\n"
                            desc += f"**▶ {curr_line}**\n"
                            if next_line:
                                desc += f"*{next_line}*"

                        embed.description = desc

                        try:
                            await msg.edit(embed=embed)
                            last_edit_time = time.time()
                        except discord.errors.HTTPException:
                            pass

                # 將檢測頻率提升為 0.5 秒，使切歌或結束的感知更即時
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # 外部強制取消時安全退出
            pass
        except Exception as e:
            print(f"Sync Lyrics Task Error: {e}")
        finally:
            # 確保任務結束時提供視覺回饋
            embed.description = "🛑 播放結束或已切換歌曲，動態歌詞停止。"
            try:
                await msg.edit(embed=embed)
            except:
                pass
