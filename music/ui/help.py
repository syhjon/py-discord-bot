# music/ui/help.py - 定義幫助指令的分頁控制功能
from typing import List
import discord


class HelpPagination(discord.ui.View):
    """用於瀏覽幫助說明 Embed 的分頁控制按鈕介面。"""

    def __init__(self, embeds: List[discord.Embed]) -> None:
        """初始化分頁幫助狀態。

        Args:
            embeds (List[discord.Embed]): 待顯示的幫助說明 Embed 有序列表。

        Returns:
            None.

        Notes:
            設定 `timeout=60.0`，若閒置超過時間按鈕將會失效。
        """
        super().__init__(timeout=60.0)
        self.embeds = embeds
        self.current_page: int = 0
        self.update_buttons()

    def update_buttons(self) -> None:
        """根據目前頁碼更新分頁按鈕的啟用狀態。

        Returns:
            None.

        Notes:
            當處於第一頁時停用「上一頁」，當處於最後一頁時停用「下一頁」。
            此方法假設 `children` 列表中的前兩個子元件分別為「上一頁」與「下一頁」。
        """
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == len(self.embeds) - 1

    @discord.ui.button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換幫助視圖至上一頁。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            此動作會原地編輯現有的幫助訊息，並更新按鈕狀態。
        """
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )

    @discord.ui.button(label="下一頁 ➡️", style=discord.ButtonStyle.primary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換幫助視圖至下一頁。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 觸發此回呼的按鈕組件。

        Returns:
            None.

        Notes:
            此動作會原地編輯現有的幫助訊息，並更新按鈕狀態。
        """
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )
