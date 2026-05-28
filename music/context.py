# music/context.py - 斜線指令互動相容性輔助模組
from __future__ import annotations

from typing import Any

import discord


class InteractionContext:
    """為仍然依賴傳統指令上下文 (Command Context) 的程式碼所設計的輕量相容性包裝器 (Wrapper)。"""

    def __init__(
        self, interaction: discord.Interaction, *, ephemeral: bool = True
    ) -> None:
        """初始化互動上下文。

        Args:
            interaction (discord.Interaction): Discord 斜線指令的互動實例。
            ephemeral (bool): 預設是否發送僅觸發者可見的私密訊息。預設為 True。
        """
        self.interaction = interaction
        self.bot = interaction.client
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.author = interaction.user
        self.default_ephemeral = ephemeral

    @property
    def voice_client(self) -> Any:
        """取得當前伺服器的語音客戶端 (Voice Client) 實例。"""
        if not self.guild:
            return None
        return self.guild.voice_client

    async def send(self, content: str | None = None, **kwargs: Any) -> Any:
        """發送訊息。

        此方法會自動判斷目前的互動狀態，選擇使用初始回應 (response) 或後續追蹤 (followup)，
        以避免「已回應過 (Already acknowledged)」的錯誤。

        Args:
            content (str | None): 要發送的訊息內容。
            **kwargs: 傳遞給發送方法的其他關鍵字引數 (如 embed, view 等)。

        Returns:
            Any: 回傳已發送的訊息物件 (WebhookMessage)，支援後續的 .edit() 動畫操作。
        """
        # 若呼叫時無特別指定，則使用類別初始化時的預設私密狀態
        ephemeral = kwargs.pop("ephemeral", self.default_ephemeral)

        # 如果這個 interaction 已經被回應過，則必須使用 followup 傳送後續訊息
        if self.interaction.response.is_done():
            return await self.interaction.followup.send(
                content=content, ephemeral=ephemeral, wait=True, **kwargs
            )

        # 如果是第一次回應，正常使用 send_message
        await self.interaction.response.send_message(
            content=content, ephemeral=ephemeral, **kwargs
        )

        # 取得並回傳剛剛發送出去的原始回應物件，以完美相容舊有的 msg.edit() 邏輯
        return await self.interaction.original_response()

    async def send_public(self, content: str | None = None, **kwargs: Any) -> Any:
        """強制發送一則所有人皆可見的公開訊息至當前頻道。

        Args:
            content (str | None): 要發送的公開訊息內容。
            **kwargs: 其他引數。

        Returns:
            Any: 該頻道回傳的訊息物件。若找不到頻道則回傳 None。
        """
        if not self.channel:
            return None
        return await self.channel.send(content=content, **kwargs)
