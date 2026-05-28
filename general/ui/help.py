# general/ui/help.py - 幫助指令的分頁控制介面模組
"""
機器人幫助指令的分頁控制介面 (Help pagination controls) 模組。

此模組定義了基於 `discord.ui.View` 的互動式分頁元件 (Pagination View)，
提供上一頁與下一頁的按鈕，讓使用者能方便地瀏覽資料量較多、已被分割成
多個 Embed 的指令列表。
"""

from typing import List

import discord


class HelpPagination(discord.ui.View):
    """
    用於瀏覽幫助說明 Embed 的分頁控制按鈕介面。

    繼承自 `discord.ui.View`，負責管理分頁的狀態 (目前頁碼) 並處理
    使用者點擊按鈕時的非同步互動邏輯 (Interaction)。

    Attributes:
        embeds (List[discord.Embed]): 準備進行分頁顯示的 Embed 陣列。
        current_page (int): 目前顯示的頁面索引 (從 0 開始計數)。
    """

    def __init__(self, embeds: List[discord.Embed]) -> None:
        """
        初始化分頁控制介面。

        Args:
            embeds (List[discord.Embed]): 欲分頁顯示的 Discord Embed 陣列。
        """
        # 設定 UI 視圖的超時時間為 60 秒，超時後按鈕將無法再被點擊
        super().__init__(timeout=60.0)
        self.embeds = embeds
        self.current_page: int = 0

        # 初始化時先評估一次按鈕的啟用狀態 (例如第一頁時應禁用上一頁按鈕)
        self.update_buttons()

    def update_buttons(self) -> None:
        """
        根據當前的頁碼狀態，動態更新按鈕的啟用與禁用 (Disabled) 狀態。

        由於 `self.children` 依序儲存了 UI 元件中的子項目：
        - `self.children[0]` 為「上一頁」按鈕
        - `self.children[1]` 為「下一頁」按鈕
        若目前位於第一頁，則禁用「上一頁」；若位於最後一頁，則禁用「下一頁」。
        """
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.embeds) - 1

    @discord.ui.button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        「上一頁」按鈕的互動回呼函式 (Callback)。

        當使用者點擊按鈕時觸發。會將目前的頁碼減一，重新計算按鈕狀態，
        並編輯原始訊息以顯示上一頁對應的 Embed 內容。

        Args:
            interaction (discord.Interaction): 觸發按鈕點擊的 Discord 互動事件。
            button (discord.ui.Button): 被點擊的按鈕實例。
        """
        self.current_page -= 1
        self.update_buttons()
        # 編輯訊息並傳入更新後的 Embed 與 UI 視圖 (self)
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )

    @discord.ui.button(label="下一頁 ➡️", style=discord.ButtonStyle.primary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        「下一頁」按鈕的互動回呼函式 (Callback)。

        當使用者點擊按鈕時觸發。會將目前的頁碼加一，重新計算按鈕狀態，
        並編輯原始訊息以顯示下一頁對應的 Embed 內容。

        Args:
            interaction (discord.Interaction): 觸發按鈕點擊的 Discord 互動事件。
            button (discord.ui.Button): 被點擊的按鈕實例。
        """
        self.current_page += 1
        self.update_buttons()
        # 編輯訊息並傳入更新後的 Embed 與 UI 視圖 (self)
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )
