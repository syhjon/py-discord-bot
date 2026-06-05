# music/services/lyrics.py - 歌詞查詢與顯示行為服務模組
"""
歌詞查詢、快取與動態歌詞顯示服務 (Lyrics lookup and display behaviors)。

此模組實作了音樂播放器的歌詞功能。其核心邏輯包含：
1. 依據 YouTube Video ID 嘗試讀取本地快取。
2. 結合 Gemini AI 對 YouTube 原始影片標題進行自然語言分析，精確提取歌曲與歌手名稱。
3. 透過 `LRCLIB API` 進行歌詞的精確 (get) 或模糊 (search) 查詢。
4. 針對帶有時間軸的動態歌詞 (Synced Lyrics)，啟動背景任務隨音樂播放進度實時更新 UI。
"""

import asyncio
import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Tuple

import aiohttp
import discord

from core.context import InteractionContext


class LyricsService:
    """
    處理歌詞查詢、快取與動態歌詞顯示的服務類別。

    Attributes:
        gemini (Any): 注入的 AI 服務實例，用於輔助解析複雜的 YouTube 影片標題。
    """

    def __init__(self, gemini: Any) -> None:
        """
        初始化 LyricsService 實例。

        Args:
            gemini (Any): 已配置完成的 AI 服務實例 (如 GeminiService)。
        """
        self.gemini = gemini

    async def show_current_lyrics(self, ctx: InteractionContext) -> None:
        """
        處理並顯示目前正在播放歌曲的歌詞。

        這是一個多階段 (Multi-stage) 的非同步流程：
        1. 檢查播放器狀態。
        2. 尋找本地 JSON 快取。
        3. 若無快取，請求 AI 擷取中繼資料 (Metadata)。
        4. 向 LRCLIB 發起請求。
        5. 寫入快取並切換至顯示邏輯。

        Args:
            ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        """
        # 延遲匯入以避免循環依賴 (Circular Dependency)
        from music.player import get_existing_player

        player = get_existing_player(ctx)

        # 1. 防呆：確認有歌曲正在播放
        if not player or not player.current:
            return await ctx.send("目前沒有任何歌曲正在播放。")

        # 確保本地快取資料夾存在
        lyrics_dir = os.path.join(os.getcwd(), "storage", "lyrics")
        os.makedirs(lyrics_dir, exist_ok=True)

        # 從當前歌曲資料中提取 YouTube Video ID 作為快取鍵值 (Cache Key)
        raw_url = player.current.get("webpage_url", player.current.get("url", ""))
        match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", raw_url)
        video_id = match.group(1) if match else None

        if not video_id:
            return await ctx.send(
                "❌ 無法解析目前歌曲的 YouTube ID，無法建立歌詞快取。"
            )

        cache_path = os.path.join(lyrics_dir, f"{video_id}.json")

        # 2. 檢查本地快取機制 (Local Cache Hit)
        if os.path.exists(cache_path):
            msg = await ctx.send("📂 找到本地歌詞快取，正在載入中...")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)

                # 直接進入顯示邏輯
                await self._process_and_display_lyrics(
                    ctx, msg, player, cached_data, raw_url
                )
                return
            except json.JSONDecodeError:
                # 若快取損毀，則繼續執行網路搜尋流程
                await msg.edit(content="⚠️ 快取檔案損毀，重新向網路搜尋...")
        else:
            msg = await ctx.send("🔍 正在準備搜尋歌詞...")

        # 準備進行網路搜尋前的中繼資料 (Metadata)
        raw_title = player.current.get("title", "")
        uploader = player.current.get("uploader", "")
        fetched_data = None

        # 3. 優先嘗試 AI 精準解析路徑 (AI-Assisted Parsing)
        if self.gemini and self.gemini.is_configured:
            await msg.edit(content=f"🤖 正在請 AI 解析歌曲資訊：**{raw_title}** ...")
            try:
                # 建構嚴格限制輸出格式的 Prompt，強制 AI 僅回傳 JSON 陣列
                prompt = (
                    "【系統指令：請忽略原本的友善對話設定，嚴格遵守以下輸出格式】\n"
                    "請分析以下 YouTube 影片標題與上傳者，萃取出準確的「歌曲名稱 (Track Name)」與「歌手名稱 (Artist Name)」。\n"
                    f"標題：{raw_title}\n"
                    f"上傳者：{uploader}\n"
                    "請務必「只」回傳一個 JSON 格式的陣列（Array），第 0 項是歌名，第 1 項是歌手。\n"
                    '範例輸出：["Say My Name", "Odesza"]\n'
                    '如果完全無法辨識，請回傳 ["", ""]。絕不能有任何其他說明文字或 Markdown 標記。'
                )

                # 呼叫 Gemini AI 服務
                ai_response = await self.gemini.generate_text(prompt)

                track_name, artist_name = "", ""

                # 使用 Regex 提取回覆中的 JSON 陣列結構
                match_json = re.search(r"\[(.*?)\]", ai_response, re.DOTALL)
                if match_json:
                    parsed_json = json.loads(match_json.group(0))
                    # 確保回傳的資料結構符合預期
                    if isinstance(parsed_json, list) and len(parsed_json) >= 2:
                        track_name = str(parsed_json[0]).strip()
                        artist_name = str(parsed_json[1]).strip()

                # 若 AI 成功擷取出歌名與歌手，嘗試使用 LRCLIB 的 `/get` API 進行精確配對
                if track_name and artist_name:
                    await msg.edit(
                        content=f"🔍 向資料庫請求精準配對：**{track_name}** - **{artist_name}** ..."
                    )

                    encoded_track = urllib.parse.quote(track_name)
                    encoded_artist = urllib.parse.quote(artist_name)
                    url_get = f"https://lrclib.net/api/get?track_name={encoded_track}&artist_name={encoded_artist}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url_get, timeout=10) as response:
                            if response.status == 200:
                                fetched_data = await response.json()

            except Exception as e:
                # 攔截 AI 服務可能的錯誤 (如 Rate Limit, 超時或格式異常)
                print(f"Gemini API Error (503/Timeout): {e}")
                await msg.edit(
                    content="⚠️ AI 服務目前滿載或無回應，自動啟動降級搜尋方案..."
                )
                await asyncio.sleep(1.5)

        # 4. 降級方案：傳統關鍵字模糊搜尋 (Fallback Search Path)
        # 當 AI 無法解析、API 錯誤，或是精確配對 (/get) 找不到資料時觸發
        if not fetched_data:
            # 透過 Regex 移除 YouTube 標題常見的雜訊 (如 MV, Official 等字眼)
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
                            # `/search` 會回傳列表，取第一筆最相關的結果
                            if data_list and isinstance(data_list, list):
                                fetched_data = data_list[0]
                        else:
                            return await msg.edit(
                                content=f"⚠️ LRCLIB API 發生異常 (狀態碼: {response.status})"
                            )
            except Exception as e:
                print(f"LRCLIB Search Error: {e}")
                return await msg.edit(content="⚠️ 連線至歌詞庫時發生網路錯誤。")

        # 5. 處理最終取得的資料
        if fetched_data:
            # 寫入快取，供未來相同歌曲直接讀取
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(fetched_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Cache Write Error: {e}")

            # 將資料轉交給顯示邏輯層
            await self._process_and_display_lyrics(
                ctx, msg, player, fetched_data, raw_url
            )
        else:
            await msg.edit(content="❌ 資料庫中找不到這首歌的相關歌詞。")

    async def _process_and_display_lyrics(
        self,
        ctx: InteractionContext,
        msg: discord.Message,
        player: Any,
        data: Dict[str, Any],
        raw_url: str,
    ) -> None:
        """
        處理歌詞資料並決定顯示模式。

        若資料包含帶時間軸的動態歌詞 (Synced Lyrics)，則啟動背景同步任務；
        否則退回顯示靜態純文字歌詞 (Plain Lyrics)。

        Args:
            ctx (InteractionContext): 互動上下文。
            msg (discord.Message): 要進行編輯更新的 Discord 原始訊息物件。
            player (Any): 目前的音樂播放器實例。
            data (Dict[str, Any]): 從 API 或快取取得的原始歌詞 JSON 資料。
            raw_url (str): 目前歌曲的網址，用於追蹤歌曲切換狀態。
        """
        synced_lyrics = data.get("syncedLyrics")
        plain_lyrics = data.get("plainLyrics")
        title = data.get("trackName", "未知曲目")
        artist = data.get("artistName", "未知歌手")

        # 優先處理動態歌詞 (Synced Lyrics)
        if synced_lyrics:
            parsed_lyrics = self._parse_synced_lyrics(synced_lyrics)
            if parsed_lyrics:
                # 若之前已有動態歌詞任務在運行，先將其取消，避免衝突
                if hasattr(player, "lyrics_task") and player.lyrics_task:
                    player.lyrics_task.cancel()

                # 建立並綁定新的背景同步任務到播放器實例上
                player.lyrics_task = asyncio.create_task(
                    self._sync_lyrics_task(
                        ctx, msg, player, parsed_lyrics, raw_url, title, artist
                    )
                )
                return

        # 降級處理靜態歌詞 (Plain Lyrics)
        if plain_lyrics:
            # 避免觸發 Discord Embed 的 2000 字元長度限制
            if len(plain_lyrics) > 1850:
                plain_lyrics = plain_lyrics[:1850] + "\n\n...(歌詞過長，已截斷)"

            await msg.edit(
                content=f"📜 **{title} - {artist}**\n```text\n{plain_lyrics}\n```"
            )
        else:
            await msg.edit(content="❌ 雖然找到了該歌曲，但資料庫內無可用的歌詞文本。")

    def _parse_synced_lyrics(self, raw_synced: str) -> List[Tuple[float, str]]:
        """
        解析標準 LRC 格式的動態歌詞字串。

        將 LRC 的時間標籤 (如 `[01:23.45] 歌詞內容`) 轉換為以秒為單位的浮點數。

        Args:
            raw_synced (str): 原始 LRC 格式的歌詞字串。

        Returns:
            List[Tuple[float, str]]: 包含 `(秒數, 歌詞字串)` 的 Tuple 列表。
        """
        lines = raw_synced.split("\n")
        parsed = []
        for line in lines:
            # 使用 Regex 捕捉分鐘、秒數(含小數)與後方文字
            match = re.match(r"\[(\d{2,}):(\d{2}(?:\.\d+)?)\]\s*(.*)", line.strip())
            if match:
                minutes, seconds, text = match.groups()
                # 轉換為總秒數
                time_sec = int(minutes) * 60 + float(seconds)
                # 若為空白行則使用預設音符符號，以維持時間軸連貫性
                parsed.append((time_sec, text or "🎵"))
        return parsed

    async def _sync_lyrics_task(
        self,
        ctx: InteractionContext,
        msg: discord.Message,
        player: Any,
        parsed_lyrics: List[Tuple[float, str]],
        target_url: str,
        title: str,
        artist: str,
    ) -> None:
        """
        負責動態顯示歌詞的背景非同步任務 (Background Task)。

        這個任務會持續監控播放器的當前進度，並在適當的時間點編輯 Discord 訊息，
        以達到歌詞隨音樂滾動顯示的效果 (類似 KTV)。

        Args:
            ctx (InteractionContext): 互動上下文。
            msg (discord.Message): 準備不斷被更新 (Edit) 的 Discord 訊息物件。
            player (Any): 目前的音樂播放器實例。
            parsed_lyrics (List[Tuple[float, str]]): 解析完畢的動態歌詞陣列。
            target_url (str): 啟動此任務時的歌曲網址。用於判斷是否已切歌。
            title (str): 歌曲名稱。
            artist (str): 歌手名稱。
        """
        current_index = -2
        last_edit_time = 0.0

        # 初始化動態歌詞的 Embed 容器
        embed = discord.Embed(
            title=f"🎤 動態歌詞: {title} - {artist}", color=discord.Color.blue()
        )

        # 清除前一個步驟殘留的 content 文字，並掛上新的 Embed
        await msg.edit(content=None, embed=embed)

        try:
            # 主迴圈：只要有歌曲正在播放就持續執行
            while player.current:
                # 安全檢查：若網址改變，代表已經切歌，應結束當前的歌詞追蹤任務
                current_url = player.current.get(
                    "webpage_url", player.current.get("url", "")
                )
                if current_url != target_url:
                    break

                # 檢查 Voice Client 狀態
                vc = ctx.voice_client
                if not vc or not vc.is_connected():
                    break

                # 暫停時不退出迴圈，而是等待恢復播放
                if not vc.is_playing():
                    if vc.is_paused():
                        await asyncio.sleep(0.5)
                        continue
                    break

                # 取得播放器目前的進度 (秒數)
                current_time = player.get_current_time()
                target_index = -1

                # 比對時間軸，找出目前應該顯示哪一句歌詞
                for i, (timestamp, _) in enumerate(parsed_lyrics):
                    if current_time >= timestamp:
                        target_index = i
                    else:
                        break

                # 若當前應顯示的歌詞行有變動，則進行 UI 更新
                if target_index != current_index:
                    now = time.time()
                    # 節流 (Throttling) 機制：限制每 1.5 秒最多編輯一次訊息。
                    # Discord API 的 Rate Limit 極其嚴格，頻繁編輯會導致 HTTP 429 錯誤。
                    if now - last_edit_time >= 1.5:
                        current_index = target_index
                        # 呼叫輔助函式建構上下共 5 行的滾動歌詞視野
                        embed.description = self._build_synced_lyrics_description(
                            parsed_lyrics, target_index
                        )

                        try:
                            # 執行訊息編輯
                            await msg.edit(embed=embed)
                            last_edit_time = time.time()
                        except discord.errors.HTTPException:
                            # 吞咽小幅度的網路錯誤，避免任務崩潰
                            pass

                # 等待 0.5 秒後進入下一次檢查，兼顧效能與反應速度
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # 任務被外部 (如使用者下達 /skip 或是手動請求新歌詞) 取消時，正常退出
            pass
        except Exception as e:
            # 捕捉未預期錯誤，避免影響主執行緒
            print(f"Sync Lyrics Task Error: {e}")
        finally:
            # 無論正常結束或異常中斷，皆將狀態更新為停止
            embed.description = "🛑 播放結束或已切換歌曲，動態歌詞停止。"
            try:
                await msg.edit(embed=embed)
            except Exception:
                pass

    def _build_synced_lyrics_description(
        self, parsed_lyrics: List[Tuple[float, str]], target_index: int
    ) -> str:
        """
        建構動態歌詞的視窗 (Window) 呈現字串。

        為了提供類似 KTV 的體驗，此函式會擷取當前行，並加上前 2 行與後 2 行，
        並利用 Markdown (如加粗標記) 突顯目前正在唱的部分。

        Args:
            parsed_lyrics (List[Tuple[float, str]]): 解析後的完整歌詞陣列。
            target_index (int): 目前應該高亮顯示 (Highlight) 的歌詞索引值。

        Returns:
            str: 準備放入 Embed.description 的格式化字串。
        """
        # 處理前奏 (未達第一句歌詞的時間)
        if target_index == -1:
            desc = "🎵 *(前奏中...)*\n\n"
            if parsed_lyrics:
                desc += f"即將演唱：*{parsed_lyrics[0][1]}*"
            return desc

        lines_to_show = []

        # 加入前兩行 (斜體、灰色感)
        if target_index >= 2:
            lines_to_show.append(f"*{parsed_lyrics[target_index - 2][1]}*")
        if target_index >= 1:
            lines_to_show.append(f"*{parsed_lyrics[target_index - 1][1]}*")

        # 突顯當前行 (加粗並加上指標箭頭)
        lines_to_show.append(f"**▶ {parsed_lyrics[target_index][1]}**")

        # 加入後兩行 (預告未來的歌詞)
        if target_index + 1 < len(parsed_lyrics):
            lines_to_show.append(f"*{parsed_lyrics[target_index + 1][1]}*")
        if target_index + 2 < len(parsed_lyrics):
            lines_to_show.append(f"*{parsed_lyrics[target_index + 2][1]}*")

        # 將陣列合併為單一字串，以換行符號分隔
        return "\n".join(lines_to_show)
