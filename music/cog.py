# music/cog.py - 音樂播放的主要 Cog，負責註冊指令和管理播放器
"""
此模組定義了音樂機器人的核心 Cog 類別。
透過繼承多個 Mixin 類別，將龐大的指令集與服務邏輯進行解耦與重組，
有效避免單一檔案過於龐大的「上帝物件 (God Object)」反模式，提升程式碼的可維護性。
"""

from discord.ext import commands

from music.commands import (
    AskCommandMixin,
    ClearCommandMixin,
    CutinCommandMixin,
    GgCommandMixin,
    HelpCommandMixin,
    JumpCommandMixin,
    LoopCommandMixin,
    LyricsCommandMixin,
    MuteCommandMixin,
    NowplayingCommandMixin,
    PauseCommandMixin,
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
from music.services import (
    GeminiService,
    YouTubeServiceMixin,
    create_search_ytdl,
    ensure_playlists_dir,
    get_playlists_dir,
)


class Music(
    AskCommandMixin,
    SongCommandMixin,
    QuickCommandMixin,
    CutinCommandMixin,
    PauseCommandMixin,
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
    HelpCommandMixin,
    GgCommandMixin,
    YouTubeServiceMixin,
    commands.Cog,
):
    """音樂播放與語音 AI 助理的主要 Cog 類別。

    此類別作為 `discord.py` 載入擴充功能（Extension）的進入點。
    它不直接實作具體邏輯，而是透過多重繼承 (Multiple Inheritance)
    將分散在各檔案中的指令 (Commands) 與服務 (Services) 拼裝成一個完整的模組。
    """

    def __init__(self, bot: commands.Bot) -> None:
        """初始化 Music Cog 及其所需的底層服務與資源。

        Args:
            bot (commands.Bot): Discord 機器人的核心實例，提供 API 操作與事件監聽。
        """
        self.bot: commands.Bot = bot

        # 初始化 Gemini 語音與文字問答服務
        self.gemini: GeminiService = GeminiService()

        # 初始化搜尋專用的 yt-dlp 實例（此實例為全域共用，避免重複消耗資源）
        self.ytdl = create_search_ytdl()

        # 確保個人播放清單的儲存目錄存在
        self.playlists_dir: str = get_playlists_dir(__file__)
        ensure_playlists_dir(self.playlists_dir)
