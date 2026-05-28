# core/bot.py - 自訂 Discord Bot 類別與擴充模組載入流程
"""
自訂 Discord 機器人核心類別與擴充模組 (Cogs) 載入流程。

此模組定義了繼承自 `discord.ext.commands.Bot` 的 `CustomBot` 類別，
負責集中管理環境設定 (Config)、日誌記錄 (Logging)、依賴注入容器 (Service Container)，
以及機器人啟動時的擴充模組載入與指令同步作業。
"""

from __future__ import annotations

import os
from logging import Logger
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from core.config import BotConfig
from core.container import ServiceContainer


def ensure_opus_loaded(logger: Logger) -> None:
    """確保 Discord 語音播放 PCM 音源時所需的 Opus 編碼器已載入。"""
    if discord.opus.is_loaded():
        return

    candidates = [
        os.getenv("OPUS_LIBRARY_PATH"),
        "libopus.0.dylib",
        "libopus.dylib",
        "libopus.so.0",
        "libopus.so",
        "/opt/homebrew/lib/libopus.dylib",
        "/usr/local/lib/libopus.dylib",
        "/usr/lib/libopus.so.0",
    ]

    last_error: Exception | None = None
    for candidate in candidates:
        if not candidate:
            continue

        try:
            discord.opus.load_opus(candidate)
        except OSError as e:
            last_error = e
            continue

        logger.info(f"✅ 已載入 Opus 音訊編碼器: {candidate}")
        return

    logger.warning(
        "無法自動載入 Opus 音訊編碼器；語音可連線但可能無法播放 PCM 音訊。"
        "請安裝 opus，或設定 OPUS_LIBRARY_PATH 指向 libopus。"
        f"最後錯誤: {last_error}"
    )


class CustomBot(commands.Bot):
    """
    自訂的 Discord Bot 類別。

    作為整個機器人應用程式的核心樞紐，除了標準的 Bot 功能外，
    還整合了服務容器以實作依賴注入 (Dependency Injection)，並提供
    自訂的指令同步策略與全域事件監聽。
    """

    def __init__(
        self,
        *,
        config: BotConfig,
        logger: Logger,
        services: ServiceContainer | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化 CustomBot 實例。

        Args:
            config (BotConfig): 機器人的環境設定物件。
            logger (Logger): 專用的日誌記錄器實例。
            services (ServiceContainer | None, optional): 依賴注入的服務容器。
                若未提供，則會自動建立一個空的新容器。預設為 None。
            **kwargs: 傳遞給父類別 `commands.Bot` 的其他關鍵字參數 (例如 intents)。
        """
        super().__init__(**kwargs)
        self.config = config
        self.services = services or ServiceContainer()
        self.log = logger
        self.guild_commands_synced = False

        # 綁定全域的應用程式指令 (斜線指令) 錯誤處理器
        self.tree.error(self.on_app_command_error)
        ensure_opus_loaded(self.log)

    async def clear_remote_global_commands(self) -> None:
        """
        清除 Discord 端殘留的全域斜線指令 (Global Commands)。

        由於全域指令同步到所有伺服器可能需要長達一小時，開發或部署時通常改用
        特定伺服器 (Guild) 指令來達成即時更新。此方法會先暫存目前的指令清單，
        清空 Discord 上的全域指令註冊，再將指令加回本機記憶體中，以避免在
        Discord 客戶端中看到重複的指令。
        """
        # 建立目前載入的所有指令快照
        commands_snapshot = list(self.tree.get_commands())
        if not commands_snapshot:
            return

        # 清除全域域的指令並同步至 Discord
        self.tree.clear_commands(guild=None)
        cleared = await self.tree.sync()

        # 將指令重新加回本機的 CommandTree，但不推送到全域
        for command in commands_snapshot:
            self.tree.add_command(command, override=True)

        self.log.info(
            f"✅ 已清除 {len(cleared)} 個全域斜線指令；目前改用伺服器即時同步。"
        )

    async def setup_hook(self) -> None:
        """
        Discord.py 的非同步啟動掛勾 (Setup Hook)。

        在機器人登入 Discord 後但開始接收事件 (on_ready) 之前，會自動呼叫此方法。
        主要負責載入所有的 Cogs 模組，並根據設定檔決定如何同步斜線指令。
        """
        # 載入所有擴充模組
        await self.load_extensions()

        # 若有設定特定的伺服器 ID，則僅將指令同步至該伺服器以實現即時更新
        if self.config.guild_id:
            try:
                guild = discord.Object(id=int(self.config.guild_id))
            except ValueError:
                self.log.error("DISCORD_GUILD_ID 必須是 Discord 伺服器 ID 的數字。")
            else:
                await self.clear_remote_global_commands()
                # 將本機的全域指令複製到指定的伺服器 CommandTree 中並同步
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                self.log.info(f"✅ 已同步 {len(synced)} 個伺服器斜線指令。")
                return

        self.log.info(
            "未設定 DISCORD_GUILD_ID，將在 on_ready 對已加入的伺服器同步斜線指令。"
        )

    async def load_extensions(self) -> None:
        """
        動態載入 `cogs` 目錄下的所有 Cog 擴充模組檔案。

        會掃描專案根目錄下的 `./cogs` 資料夾，自動載入所有以 `.py` 結尾且
        非底線 (`_`) 開頭的模組檔案。
        """
        for filename in sorted(os.listdir("./cogs")):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue

            # 移除 '.py' 副檔名後載入模組
            await self.load_extension(f"cogs.{filename[:-3]}")
            self.log.info(f"✅ 已載入模組: {filename}")

    async def on_ready(self) -> None:
        """
        連線就緒事件處理器。

        當 Discord 標記機器人為就緒狀態後觸發。此方法會：
        1. 記錄啟動與連線成功的日誌。
        2. 若在 setup_hook 中未完成指定伺服器的指令同步，則對機器人加入的所有伺服器進行同步。
        3. 在每個加入的伺服器中尋找適合的文字頻道，發送系統重新上線的通知。
        """
        self.log.info("====================================")
        self.log.info(f"登入成功！機器人 {self.user} 已經上線。")
        self.log.info("全域事件監聽器已啟動。")
        self.log.info("====================================")

        # fallback 機制：若未指定單一伺服器，則逐一將指令推送到所有已加入的伺服器
        if not self.config.guild_id and not self.guild_commands_synced:
            await self.clear_remote_global_commands()

            for guild in self.guilds:
                guild_object = discord.Object(id=guild.id)
                self.tree.copy_global_to(guild=guild_object)
                synced = await self.tree.sync(guild=guild_object)
                self.log.info(
                    f"✅ 已在伺服器 [{guild.name}] 同步 {len(synced)} 個斜線指令。"
                )
            self.guild_commands_synced = True

        # 遍歷所有伺服器以發送上線通知
        for guild in self.guilds:
            # 優先嘗試系統預設頻道
            target_channel = guild.system_channel

            # 若無系統頻道或機器人無發言權限，則尋找第一個可發言的文字頻道
            if (
                not target_channel
                or not target_channel.permissions_for(guild.me).send_messages
            ):
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        break

            # 發送格式化的上線通知 Embed
            if target_channel:
                try:
                    embed = discord.Embed(
                        title="🟢 系統重啟完畢",
                        description="各位好，音樂機器人已重新上線為您服務！\n請隨時輸入 `/help` 查看音樂指令。",
                        color=discord.Color.green(),
                    )
                    await target_channel.send(embed=embed)
                    self.log.info(
                        f"已在伺服器 [{guild.name}] 的頻道 [{target_channel.name}] 發送上線通知。"
                    )
                except Exception as e:
                    self.log.error(f"無法在伺服器 [{guild.name}] 發送上線通知: {e}")

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """
        全域斜線指令錯誤處理器。

        捕捉任何在執行斜線指令期間未被處理的例外 (Exception)，記錄錯誤詳細資訊，
        並回傳一個對使用者友善且僅自己可見 (ephemeral) 的錯誤提示。

        Args:
            interaction (discord.Interaction): 觸發錯誤的互動事件。
            error (app_commands.AppCommandError): 拋出的例外物件。
        """
        self.log.error(f"執行斜線指令時發生錯誤: {error}", exc_info=True)
        message = "⚠️ 執行指令時發生錯誤，請稍後再試。"

        # 確保根據目前的互動回應狀態，使用正確的方式回傳錯誤訊息
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    def dispatch(self, event_name: str, /, *args: Any, **kwargs: Any) -> None:
        """
        事件分派攔截器 (Event Dispatch Interceptor)。

        覆寫內建的分派機制以實現事件層級的監控。除了過濾掉背景高頻且雜訊過多的
        Socket 網路層事件外，其餘事件觸發時皆會留下日誌記錄。

        Args:
            event_name (str): 觸發的事件名稱 (不含 'on_' 前綴)。
            *args: 傳遞給事件處理器的位置參數。
            **kwargs: 傳遞給事件處理器的關鍵字參數。
        """
        # 定義需要過濾不記錄的底層/高頻事件
        ignore_events = ["socket_raw_receive", "socket_raw_send", "socket_response"]

        if event_name not in ignore_events:
            self.log.info(f"[事件攔截]觸發事件: on_{event_name}")

        super().dispatch(event_name, *args, **kwargs)


def create_bot(
    *,
    config: BotConfig,
    logger: Logger,
    services: ServiceContainer | None = None,
) -> CustomBot:
    """
    機器人實例的工廠函式 (Factory Function)。

    負責設定機器人所需的基礎 Intents，並使用傳入的依賴實例化 CustomBot。

    Args:
        config (BotConfig): 機器人的環境設定。
        logger (Logger): 日誌記錄器。
        services (ServiceContainer | None, optional): 服務容器。預設為 None。

    Returns:
        CustomBot: 設定完成的自訂機器人實例。
    """
    # 建立預設的 Intents 配置
    intents = discord.Intents.default()
    # 為了隱私與安全性，明確關閉訊息內容讀取權限 (若只依賴斜線指令則不需要此權限)
    intents.message_content = False

    return CustomBot(
        config=config,
        services=services,
        logger=logger,
        # 斜線指令為主，不使用傳統前綴指令
        command_prefix=commands.when_mentioned,
        intents=intents,
        # 移除 Discord.py 預設的文字幫助指令，交由自訂的 /help 處理
        help_command=None,
    )
