# music/__init__.py - 標記並初始化 music 套件
"""
此模組為 `music` 套件的根目錄初始化檔案。

它將目前目錄標記為一個標準的 Python 套件，使得專案中的其他模組可以透過點語法
(例如 `from music.player import get_player`) 來匯入底下的子模組。

此套件只包含音樂播放相關的核心業務邏輯，包含但不限於：
- `player`: 音樂播放、佇列管理與狀態控制的核心邏輯。
- `commands`: 音樂 slash commands，負責把互動指向服務層行為。
- `services`: 音樂行為與外部 API (如 YouTube、LRCLIB) 整合。
- `ui`: 定義 Discord 互動式元件 (如 View、Select、Button)。
- `utils`: 提供時間格式化、進度條等共用工具函式。
"""
