import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playlists import save_current_queue


class SavePlaylistCommandMixin:
    """提供儲存播放清單指令的 Mixin 類別。"""

    @app_commands.command(
        name="saveplaylist", description="將目前的播放佇列儲存為個人播放清單"
    )
    @app_commands.describe(playlist_name="播放清單名稱")
    async def saveplaylist_command(
        self, interaction: discord.Interaction, playlist_name: str
    ) -> None:
        """將目前的播放狀態（包含目前歌曲與佇列）儲存為單一獨立的播放清單檔案。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            playlist_name (Optional[str]): 欲儲存的播放清單名稱。

        Returns:
            None.

        Notes:
            檔案將會儲存在 `storage/playlists/` 目錄下，命名格式為 `{user_id}_{playlist_name}.json`，
            以此確保每位使用者的播放清單獨立且不會互相覆蓋。
        """
        await save_current_queue(InteractionContext(interaction), playlist_name)
