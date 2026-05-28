# music/commands/__init__.py - 匯出音樂 Cog 所需的所有指令 Mixin 類別
"""
此模組為 `music.commands` 套件的初始化檔案。

負責集中匯出音樂機器人各類功能指令的 Mixin 類別。透過 Mixin 設計模式，
我們將龐大的 Music Cog 功能拆解為單一職責的獨立模組，以避免出現
「上帝物件 (God Object)」的反模式，確保系統的高維護性與擴充性。

Example:
    >>> from music.commands import PlayCommandMixin, StopCommandMixin
"""

from .ask import AskCommandMixin
from .clear import ClearCommandMixin
from .cutin import CutinCommandMixin
from .gg import GgCommandMixin
from .help import HelpCommandMixin
from .jump import JumpCommandMixin
from .loop import LoopCommandMixin
from .lyrics import LyricsCommandMixin
from .mute import MuteCommandMixin
from .nowplaying import NowplayingCommandMixin
from .pause import PauseCommandMixin
from .playat import PlayatCommandMixin
from .playplaylist import PlayPlaylistCommandMixin
from .previous import PreviousCommandMixin
from .progress import ProgressCommandMixin
from .queue import QueueCommandMixin
from .quick import QuickCommandMixin
from .remove import RemoveCommandMixin
from .resume import ResumeCommandMixin
from .saveplaylist import SavePlaylistCommandMixin
from .seek import SeekCommandMixin
from .shuffle import ShuffleCommandMixin
from .skip import SkipCommandMixin
from .song import SongCommandMixin
from .stop import StopCommandMixin
from .sysinfo import SysInfoCommandMixin
from .unmute import UnmuteCommandMixin
from .voldown import VoldownCommandMixin
from .volume import VolumeCommandMixin
from .volumecheck import VolumecheckCommandMixin
from .volup import VolupCommandMixin

# 定義公開介面，確保匯入時路徑清晰
__all__ = [
    "AskCommandMixin",
    "ClearCommandMixin",
    "CutinCommandMixin",
    "GgCommandMixin",
    "HelpCommandMixin",
    "JumpCommandMixin",
    "LoopCommandMixin",
    "LyricsCommandMixin",
    "MuteCommandMixin",
    "NowplayingCommandMixin",
    "PauseCommandMixin",
    "PlayatCommandMixin",
    "PlayPlaylistCommandMixin",
    "PreviousCommandMixin",
    "ProgressCommandMixin",
    "QueueCommandMixin",
    "QuickCommandMixin",
    "RemoveCommandMixin",
    "ResumeCommandMixin",
    "SavePlaylistCommandMixin",
    "SeekCommandMixin",
    "ShuffleCommandMixin",
    "SkipCommandMixin",
    "SongCommandMixin",
    "StopCommandMixin",
    "SysInfoCommandMixin",
    "UnmuteCommandMixin",
    "VoldownCommandMixin",
    "VolumeCommandMixin",
    "VolumecheckCommandMixin",
    "VolupCommandMixin",
]
