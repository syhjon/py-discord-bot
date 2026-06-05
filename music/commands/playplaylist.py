import discord
from discord import app_commands

from core.context import InteractionContext
from music.services.playlists import play_saved_playlist


class PlayPlaylistCommandMixin:
    """提供播放清單載入指令的 Mixin 類別。"""

    @app_commands.command(
        name="playplaylist", description="載入並播放您儲存的個人播放清單"
    )
    @app_commands.describe(playlist_name="要載入的播放清單名稱")
    async def playplaylist_command(
        self, interaction: discord.Interaction, playlist_name: str
    ) -> None:
        """載入儲存的播放清單並將歌曲加入佇列。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            playlist_name (Optional[str]): 要載入的播放清單名稱。

        Returns:
            None.

        Notes:
            配合新的儲存架構，此指令會讀取 `storage/playlists/` 目錄下以 `{user_id}_{playlist_name}.json`
            命名的獨立檔案。佇列中的網址會在播放器迴圈進行串流解析時即時處理。
        """
        await play_saved_playlist(
            InteractionContext(interaction),
            playlist_name,
            search_service=self.youtube_service,
        )
