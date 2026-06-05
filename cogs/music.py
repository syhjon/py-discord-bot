# cogs/music.py - 音樂播放的 Discord Cog
"""
Discord 音樂播放功能的展示層 (Presentation Layer) 擴充模組。

此模組定義了音樂機器人的核心 Cog 類別。它負責註冊所有與音樂相關的
Discord Slash Commands，並透過依賴注入 (Dependency Injection) 容器
接收外部服務的實作 (例如 AI 服務與音樂搜尋服務)。
"""

import asyncio
from typing import cast

import discord
from discord.ext import commands

from core.bot import CustomBot
from domain import IAIService, IMusicSearchService
from music.commands import (
    ClearCommandMixin,
    CutinCommandMixin,
    GgCommandMixin,
    JumpCommandMixin,
    LoopCommandMixin,
    LyricsCommandMixin,
    MuteCommandMixin,
    NowplayingCommandMixin,
    PauseCommandMixin,
    PlayerCommandMixin,
    PlayatCommandMixin,
    PlayPlaylistCommandMixin,
    PreviousCommandMixin,
    ProgressCommandMixin,
    QueueCommandMixin,
    QuickCommandMixin,
    RemoveCommandMixin,
    ResumeCommandMixin,
    SavePlaylistCommandMixin,
    SeekCommandMixin,
    ShuffleCommandMixin,
    SkipCommandMixin,
    SongCommandMixin,
    StopCommandMixin,
    UnmuteCommandMixin,
    VoldownCommandMixin,
    VolumeCommandMixin,
    VolumecheckCommandMixin,
    VolupCommandMixin,
)
from music.player import players
from music.services import ensure_playlists_dir, get_playlists_dir
from music.services.lyrics import LyricsService
from music.services.youtube import YouTubeServiceMixin


class Music(
    SongCommandMixin,
    QuickCommandMixin,
    CutinCommandMixin,
    PauseCommandMixin,
    PlayerCommandMixin,
    ResumeCommandMixin,
    StopCommandMixin,
    SkipCommandMixin,
    PreviousCommandMixin,
    ClearCommandMixin,
    RemoveCommandMixin,
    ShuffleCommandMixin,
    LoopCommandMixin,
    VolumeCommandMixin,
    VolupCommandMixin,
    VoldownCommandMixin,
    VolumecheckCommandMixin,
    MuteCommandMixin,
    UnmuteCommandMixin,
    SeekCommandMixin,
    JumpCommandMixin,
    PlayatCommandMixin,
    QueueCommandMixin,
    NowplayingCommandMixin,
    ProgressCommandMixin,
    LyricsCommandMixin,
    SavePlaylistCommandMixin,
    PlayPlaylistCommandMixin,
    GgCommandMixin,
    YouTubeServiceMixin,
    commands.Cog,
):
    """
    音樂播放的主要 Cog 類別。

    透過多重繼承 (Multiple Inheritance) 整合了所有個別的音樂指令 (Mixins)
    與 YouTube 服務邏輯，並作為標準的 `commands.Cog` 掛載至機器人中。
    """

    def __init__(
        self,
        bot: commands.Bot,
        ai_service: IAIService | None = None,
        youtube_service: IMusicSearchService | None = None,
    ) -> None:
        """
        初始化 Music Cog 並配置所需的服務與目錄。

        Args:
            bot (commands.Bot): Discord 機器人實例。
            ai_service (IAIService | None, optional): 注入的 AI 服務實例。
                若未提供，則從服務容器中自動提取。預設為 None。
            youtube_service (IMusicSearchService | None, optional): 注入的音樂搜尋服務實例。
                若未提供，則從服務容器中自動提取。預設為 None。
        """
        self.bot = bot
        services = cast(CustomBot, bot).services

        # 若未明確傳入服務，則從自訂機器人的依賴注入容器中取得
        if ai_service is None:
            ai_service = services.ai
        if youtube_service is None:
            youtube_service = services.youtube

        self.ai_service = ai_service
        self.youtube_service = youtube_service

        # 為了保持與既有 command/service helper 的向下相容性，
        # 將這些服務綁定到原有的屬性名稱上。
        self.gemini = ai_service
        self.ytdl = youtube_service.ytdl
        self.lyrics_service = LyricsService(ai_service)

        # 初始化並確保本地的播放清單儲存目錄存在
        self.playlists_dir = get_playlists_dir(__file__)
        ensure_playlists_dir(self.playlists_dir)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        全域的互動檢查 (Interaction Check)。

        在執行任何此 Cog 內的斜線指令 (Slash Command) 前會先觸發此檢查，
        用於限制音樂相關指令只能在 Discord 的伺服器 (Guild) 頻道內使用，
        防止在私人訊息 (DM) 中觸發導致錯誤。

        Args:
            interaction (discord.Interaction): 觸發指令的互動事件。

        Returns:
            bool: 若在伺服器內則回傳 True 允許執行，否則回傳 False 並傳送錯誤提示。
        """
        if interaction.guild is not None:
            return True

        # 若在私人訊息中使用，則以僅限使用者可見 (ephemeral) 的方式回傳錯誤
        await interaction.response.send_message(
            "❌ 音樂指令只能在伺服器頻道中使用。", ephemeral=True
        )
        return False

    async def cog_unload(self) -> None:
        """
        資源清理邏輯。

        當此 Cog 被重新載入、卸載，或是機器人關閉時，Discord.py 會自動呼叫此方法。
        負責安全地關閉並清理所有活躍中的音樂播放器，避免產生懸空連線或資源外洩。
        """
        # 收集所有播放器的清理任務 (非同步)
        cleanup_tasks = [player.cleanup() for player in players.values()]

        if cleanup_tasks:
            # 並行執行所有清理任務，並忽略單一任務可能產生的例外錯誤以確保流程走完
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # 清空全域的播放器暫存字典
        players.clear()
        print("✅ 音樂播放系統已安全卸載，所有連線與程序皆已關閉。")


async def setup(bot: commands.Bot) -> None:
    """
    Cog 的非同步載入函式 (Setup function)。

    Discord.py 載入擴充模組時會自動呼叫此函式。它負責從機器人的服務容器中
    提取並轉型出必要的服務實例，接著將初始化後的 `Music` Cog 註冊至機器人中。

    Args:
        bot (commands.Bot): Discord 機器人實例。
    """
    services = cast(CustomBot, bot).services
    ai_service = services.ai
    youtube_service = services.youtube

    # 注入服務並將 Cog 加入機器人中
    await bot.add_cog(Music(bot, ai_service, youtube_service))
