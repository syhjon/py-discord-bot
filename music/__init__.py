# music/__init__.py - 標記並初始化 music 套件
"""
此模組為 `music` 套件的根目錄初始化檔案。

它將當前目錄標記為一個標準的 Python 套件，使得專案中的其他模組可以透過點語法
(例如 `from music.player import get_player`) 來匯入底下的子模組。

此套件包含了音樂機器人的所有核心業務邏輯，包含但不限於：
- `cogs`: 註冊於 Discord 機器人的指令與事件監聽器。
- `player`: 音樂播放、佇列管理與狀態控制的核心邏輯。
- `services`: 處理與外部 API (如 YouTube、Gemini) 互動的服務層。
- `ui`: 定義 Discord 互動式元件 (如 View、Select、Button)。
- `utils`: 提供時間格式化、進度條等共用工具函式。
"""
