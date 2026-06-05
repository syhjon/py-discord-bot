# music/ui/controls.py - 固定播放器面板、按鈕控制與私人點歌介面
import random
from typing import Any

import discord

from core.context import InteractionContext


class AddSongModal(discord.ui.Modal):
    """讓使用者透過播放器面板輸入歌曲名稱或 YouTube 網址。"""

    query = discord.ui.TextInput(
        label="歌曲名稱或 YouTube 網址",
        placeholder="輸入歌名、關鍵字或 YouTube 連結",
        max_length=300,
        required=True,
    )

    def __init__(self, player: Any) -> None:
        """初始化播放器點歌表單。

        Args:
            player (Any): 接收點歌請求的 `MusicPlayer` 實例。

        Returns:
            None.
        """
        super().__init__(title="點歌")
        self.player = player

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """處理點歌表單送出後的搜尋與加入佇列流程。

        Args:
            interaction (discord.Interaction): 使用者送出表單時產生的互動事件。

        Returns:
            None.
        """
        if not self.player.search_service:
            return await interaction.response.send_message(
                "❌ 目前播放器沒有可用的搜尋服務，請改用 `/song` 或 `/quick`。",
                ephemeral=True,
            )

        from music.services.playback import process_track_request

        ctx = InteractionContext(interaction, ephemeral=True)
        await process_track_request(
            ctx,
            str(self.query.value),
            self.player.search_service,
            is_cutin=False,
            fetch_count=1,
            use_select_menu=False,
        )


class PlayerControls(discord.ui.View):
    """固定播放器面板使用的互動式控制按鈕視圖。"""

    def __init__(
        self,
        player: Any,
        *,
        owner_id: int | None = None,
        page: int = 0,
        timeout: float | None = None,
    ) -> None:
        """初始化播放器控制介面。

        Args:
            player (Any): 該視圖所控制的 `MusicPlayer` 實例。
            owner_id (int | None, optional): 若指定，只有該 Discord 使用者 ID 可操作此視圖。
                私人播放器面板會設定此值；公開面板則保持為 None。
            page (int, optional): 待播歌單目前顯示的 0-based 頁碼。預設為 0。
            timeout (float | None, optional): View 逾時秒數。公開面板使用 None 以保持可用；
                Discord 會自動限制 ephemeral 訊息的實際存活時間。

        Returns:
            None.
        """
        super().__init__(timeout=timeout)
        self.player = player
        self.owner_id = owner_id
        self.page = self.player.clamp_queue_page(page)
        self._sync_button_states()

    def disable_all_controls(self) -> None:
        """停用此 View 中的所有互動控制。

        Returns:
            None.
        """
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """檢查是否允許此使用者操作面板。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。

        Returns:
            bool: 允許操作時為 True；否則會發送僅該使用者可見的提示並回傳 False。
        """
        if not self._is_current_registered_panel(interaction):
            await interaction.response.send_message(
                "❌ 這個播放器面板已失效，請使用最新的面板。",
                ephemeral=True,
            )
            return False

        if self.owner_id is None or interaction.user.id == self.owner_id:
            return True

        await interaction.response.send_message(
            "❌ 這個私人播放器面板不是給你操作的。", ephemeral=True
        )
        return False

    def _is_current_registered_panel(self, interaction: discord.Interaction) -> bool:
        """確認此 View 仍是播放器目前登記中的有效面板。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。

        Returns:
            bool: 此互動訊息與 View 皆為目前最新面板時回傳 True。
        """
        if not interaction.message:
            return False

        message_id = interaction.message.id
        public_message = self.player.panel_message
        private_message = self.player.private_panel_message

        if public_message and message_id == public_message.id:
            return self.player.panel_view is self
        if private_message and message_id == private_message.id:
            return self.player.private_panel_view is self
        if not public_message and not private_message:
            return (
                self.player.panel_view is self
                or self.player.private_panel_view is self
            )
        return False

    async def _ensure_active(self, interaction: discord.Interaction) -> bool:
        """確認播放器仍然存在且可控制。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。

        Returns:
            bool: 播放器可控制時回傳 True；否則會停用面板並回傳 False。
        """
        if self.player.is_active:
            return True

        self.disable_all_controls()
        if interaction.response.is_done():
            await interaction.followup.send("播放器已停止。", ephemeral=True)
        else:
            await interaction.response.edit_message(
                content="播放器已停止。",
                embed=None,
                view=self,
            )
        return False

    def _is_public_panel_interaction(self, interaction: discord.Interaction) -> bool:
        """判斷目前互動是否來自播放器持有的公開面板訊息。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。

        Returns:
            bool: 互動訊息與播放器公開面板訊息相同時回傳 True。
        """
        return bool(
            self.player.panel_message
            and interaction.message
            and interaction.message.id == self.player.panel_message.id
        )

    async def _refresh_public_panel_if_needed(
        self,
        interaction: discord.Interaction,
        status_msg: str,
    ) -> None:
        """若公開面板仍存在，於私人面板操作後同步公開面板。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            status_msg (str): 公開面板頁尾要顯示的操作狀態。

        Returns:
            None.
        """
        if (
            self.player.panel_message
            and not self._is_public_panel_interaction(interaction)
        ):
            await self.player.refresh_public_panel(status_msg)

    async def _edit_panel(
        self,
        interaction: discord.Interaction,
        status_msg: str,
    ) -> None:
        """依目前狀態原地更新觸發互動的播放器面板。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            status_msg (str): 顯示於面板頁尾的操作狀態文字。

        Returns:
            None.
        """
        self.page = self.player.clamp_queue_page(self.page)
        if self._is_public_panel_interaction(interaction):
            self.player.panel_page = self.page

        self._sync_button_states()
        embed = self.player.build_panel_embed(page=self.page, status_msg=status_msg)
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.HTTPException:
            await self._send_fallback_status(interaction, status_msg)
        await self._refresh_public_panel_if_needed(interaction, status_msg)

    async def _acknowledge_terminal_stop(
        self,
        interaction: discord.Interaction,
        status_msg: str,
    ) -> None:
        """回覆即將停止播放器的操作，避免與公開面板刪除產生競態。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            status_msg (str): 顯示給使用者的停止狀態文字。

        Returns:
            None.
        """
        self.disable_all_controls()
        if self._is_public_panel_interaction(interaction):
            await interaction.response.send_message(status_msg, ephemeral=True)
        else:
            await interaction.response.edit_message(
                content=status_msg,
                embed=None,
                view=self,
            )

    async def _send_fallback_status(
        self,
        interaction: discord.Interaction,
        status_msg: str,
    ) -> None:
        """在原地編輯面板失敗時回覆一則短狀態訊息。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            status_msg (str): 要回覆的操作狀態。

        Returns:
            None.
        """
        if interaction.response.is_done():
            await interaction.followup.send(status_msg, ephemeral=True)
        else:
            await interaction.response.send_message(status_msg, ephemeral=True)

    def _sync_button_states(self) -> None:
        """依播放器狀態同步各按鈕的啟用與停用狀態。

        Returns:
            None.
        """
        active = self.player.is_active
        page_count = self.player.get_queue_page_count()

        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = not active

        self._set_button_disabled(
            "player:add_song",
            not active or not self.player.search_service,
        )
        self._set_button_disabled(
            "player:previous",
            not active or not self.player.history,
        )
        self._set_button_disabled(
            "player:next",
            not active or not self.player.current,
        )
        self._set_button_disabled(
            "player:skip",
            not active or not self.player.current,
        )
        self._set_button_disabled(
            "player:shuffle",
            not active or len(self.player.queue) < 2,
        )
        self._set_button_disabled(
            "player:queue_prev",
            not active or page_count <= 1 or self.page <= 0,
        )
        self._set_button_disabled(
            "player:queue_next",
            not active or page_count <= 1 or self.page >= page_count - 1,
        )

    def _set_button_disabled(self, custom_id: str, disabled: bool) -> None:
        """依 custom_id 設定指定按鈕是否停用。

        Args:
            custom_id (str): 目標 Discord UI 按鈕的 custom_id。
            disabled (bool): 是否停用該按鈕。

        Returns:
            None.
        """
        for child in self.children:
            if getattr(child, "custom_id", None) == custom_id:
                child.disabled = disabled
                return

    @discord.ui.button(
        label="點歌",
        emoji="➕",
        style=discord.ButtonStyle.success,
        custom_id="player:add_song",
        row=0,
    )
    async def add_song(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """開啟點歌輸入表單。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return
        if not self.player.search_service:
            return await interaction.response.send_message(
                "❌ 目前沒有可用的搜尋服務。", ephemeral=True
            )

        await interaction.response.send_modal(AddSongModal(self.player))

    @discord.ui.button(
        label="播放/暫停",
        emoji="⏯️",
        style=discord.ButtonStyle.primary,
        custom_id="player:pause_resume",
        row=0,
    )
    async def pause_resume(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換播放器於暫停與播放狀態之間。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        vc = self.player.guild.voice_client
        if not vc:
            return await self._edit_panel(interaction, "❌ 目前沒有語音連線。")

        if vc.is_paused():
            vc.resume()
            self.player.resume_time()
            await self._edit_panel(interaction, "▶️ 已繼續播放。")
        elif vc.is_playing():
            vc.pause()
            self.player.pause_time()
            await self._edit_panel(interaction, "⏸️ 已暫停播放。")
        else:
            await self._edit_panel(interaction, "⚠️ 目前沒有正在播放的音訊。")

    @discord.ui.button(
        label="上一首",
        emoji="⏮️",
        style=discord.ButtonStyle.secondary,
        custom_id="player:previous",
        row=0,
    )
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換回歷史紀錄中的上一首歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        if self.player.request_previous_track():
            await self._edit_panel(interaction, "⏮️ 已切換到上一首。")
        else:
            await self._edit_panel(interaction, "⚠️ 沒有上一首歌曲紀錄。")

    @discord.ui.button(
        label="下一首",
        emoji="⏭️",
        style=discord.ButtonStyle.secondary,
        custom_id="player:next",
        row=0,
    )
    async def next_track(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """切換到待播佇列中的下一首歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        will_stop = not self.player.queue and self.player.loop_mode == 0
        if self.player.request_next_track():
            if will_stop:
                return await self._acknowledge_terminal_stop(
                    interaction,
                    "⏭️ 已切換；沒有下一首，播放器即將停止。",
                )
            await self._edit_panel(interaction, "⏭️ 正在切換到下一首。")
        else:
            await self._edit_panel(interaction, "⚠️ 目前沒有歌曲可以切換。")

    @discord.ui.button(
        label="跳過",
        emoji="⏩",
        style=discord.ButtonStyle.secondary,
        custom_id="player:skip",
        row=0,
    )
    async def skip(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """跳過目前歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        will_stop = not self.player.queue and self.player.loop_mode == 0
        if self.player.request_next_track():
            if will_stop:
                return await self._acknowledge_terminal_stop(
                    interaction,
                    "⏩ 已跳過最後一首，播放器即將停止。",
                )
            await self._edit_panel(interaction, "⏩ 已跳過目前歌曲。")
        else:
            await self._edit_panel(interaction, "⚠️ 目前沒有歌曲可以跳過。")

    @discord.ui.button(
        label="隨機",
        emoji="🔀",
        style=discord.ButtonStyle.secondary,
        custom_id="player:shuffle",
        row=1,
    )
    async def shuffle_queue(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """隨機打亂待播佇列中的歌曲。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return
        if len(self.player.queue) < 2:
            return await self._edit_panel(
                interaction,
                "⚠️ 佇列中歌曲太少，無法隨機播放。",
            )

        random.shuffle(self.player.queue)
        self.page = 0
        await self._edit_panel(interaction, "🔀 佇列已隨機打亂。")

    @discord.ui.button(
        label="循環",
        emoji="🔁",
        style=discord.ButtonStyle.secondary,
        custom_id="player:loop",
        row=1,
    )
    async def toggle_loop(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """依序切換循環模式：關閉、單曲、佇列。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        self.player.loop_mode = (self.player.loop_mode + 1) % 3
        await self._edit_panel(
            interaction,
            f"🔁 循環模式已切換為：{self.player.get_loop_mode_label()}。",
        )

    @discord.ui.button(
        label="更新",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id="player:refresh",
        row=1,
    )
    async def update_progress(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """手動更新播放進度、狀態與歌單顯示。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        await self._edit_panel(interaction, "🔄 面板已同步。")

    @discord.ui.button(
        label="上一頁",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
        custom_id="player:queue_prev",
        row=1,
    )
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """顯示待播歌單的上一頁。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        self.page = self.player.clamp_queue_page(self.page - 1)
        await self._edit_panel(interaction, "📄 已切換歌單頁面。")

    @discord.ui.button(
        label="下一頁",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
        custom_id="player:queue_next",
        row=1,
    )
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """顯示待播歌單的下一頁。

        Args:
            interaction (discord.Interaction): Discord 按鈕互動上下文。
            button (discord.ui.Button): 被按下的按鈕元件。

        Returns:
            None.
        """
        if not await self._ensure_active(interaction):
            return

        self.page = self.player.clamp_queue_page(self.page + 1)
        await self._edit_panel(interaction, "📄 已切換歌單頁面。")
