# core/context.py - Discord 互動相容性輔助模組
"""
Discord 互動 (Interaction) 相容性輔助模組。

提供輕量級的包裝類別，將 Discord 的互動事件封裝為更易於操作的上下文 (Context) 物件，
方便底層服務層 (Service Layer) 獨立於 Discord 展示層邏輯進行呼叫與測試。
"""

from __future__ import annotations

from typing import Any

import discord


class InteractionContext:
    """
    輕量包裝斜線指令 (Slash Command) 的互動物件，供服務層使用。

    整合了常用的 Discord 屬性 (如 bot, guild, channel, author)，
    並封裝了訊息發送邏輯，自動處理互動回應 (Interaction Response) 的狀態。

    Attributes:
        interaction (discord.Interaction): 原始的 Discord 互動物件。
        bot (discord.Client): 機器人客戶端實例。
        guild (discord.Guild | None): 觸發互動的伺服器。若在私訊中觸發則為 None。
        channel (discord.abc.Messageable | None): 觸發互動的頻道。
        author (discord.User | discord.Member): 觸發互動的使用者或成員。
        default_ephemeral (bool): 預設訊息是否僅限發送者可見。
    """

    def __init__(
        self, interaction: discord.Interaction, *, ephemeral: bool = True
    ) -> None:
        """
        初始化 InteractionContext 實例。

        Args:
            interaction (discord.Interaction): 來自 Discord 的原始互動事件。
            ephemeral (bool, optional): 指定回覆訊息是否預設為僅發送者可見 (Ephemeral)。
                預設為 True，以避免指令回覆洗版。
        """
        self.interaction = interaction
        self.bot = interaction.client
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.author = interaction.user
        self.default_ephemeral = ephemeral

    @property
    def voice_client(self) -> Any:
        """
        安全取得當前伺服器的語音客戶端 (Voice Client)。

        Returns:
            Any: 若機器人已在該伺服器加入語音頻道，則回傳對應的 voice_client，否則 (或在私訊環境下) 回傳 None。
        """
        if not self.guild:
            return None
        return self.guild.voice_client

    async def send(self, content: str | None = None, **kwargs: Any) -> Any:
        """
        傳送訊息或跟進回覆 (Followup) 給使用者。

        此方法會自動檢查該互動是否已經被回應過 (`is_done()`)。
        若尚未回應，則使用 `response.send_message`；
        若已回應 (例如曾發送過「思考中...」的等待訊息)，則自動改用 `followup.send`，
        免去開發者手動判斷的麻煩。

        Args:
            content (str | None, optional): 要發送的文字內容。
            **kwargs: 傳遞給 Discord 訊息發送 API 的其他關鍵字參數 (如 embed, view 等)。

        Returns:
            Any: 成功發送後的 Discord 訊息物件 (Message)。
        """
        # 提取或使用預設的 ephemeral 設定
        ephemeral = kwargs.pop("ephemeral", self.default_ephemeral)

        # 若互動已經被回應過，必須使用 followup 發送後續訊息
        if self.interaction.response.is_done():
            return await self.interaction.followup.send(
                content=content, ephemeral=ephemeral, wait=True, **kwargs
            )

        # 若是首次回應，則使用標準的 response
        await self.interaction.response.send_message(
            content=content, ephemeral=ephemeral, **kwargs
        )
        # 回傳剛剛發送的原始訊息物件以便後續操作 (如編輯)
        return await self.interaction.original_response()

    async def send_public(self, content: str | None = None, **kwargs: Any) -> Any:
        """
        直接發送公開訊息至當前頻道。

        繞過互動事件 (Interaction) 綁定的回覆機制，直接操作所在頻道的 `send` 方法。
        適用於需要發送所有人都可見的全域通知，而不受限於 ephemeral 設定的情況。

        Args:
            content (str | None, optional): 要發送的文字內容。
            **kwargs: 傳遞給 Discord 頻道發送 API 的其他關鍵字參數。

        Returns:
            Any: 成功發送後的 Discord 訊息物件 (Message)，若無頻道上下文則回傳 None。
        """
        if not self.channel:
            return None
        return await self.channel.send(content=content, **kwargs)
