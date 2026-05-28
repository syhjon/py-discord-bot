# core/container.py - 應用程式服務容器與依賴注入輔助模組
"""
應用程式服務容器與依賴注入輔助模組 (Application service container and dependency helpers)。

提供了一個強型別的服務容器 (Service Container) 實作，用來集中註冊與解析
(Resolve) 應用程式運行時所需的各項外部服務 (如 AI、音樂搜尋)。透過依賴注入，
可以有效降低展示層 (Cogs) 與底層實作之間的耦合度。
"""

from typing import Any, Optional

from domain import IAIService, IMusicSearchService


class ServiceContainer:
    """
    強型別依賴注入容器，供 Discord 擴充模組 (Cogs) 共用。

    集中管理各種服務的實例 (Instance)，確保整個應用程式生命週期內，
    各個模組皆能取得一致且已初始化的服務物件。
    """

    def __init__(self) -> None:
        """初始化空的服務容器，將各項服務預設為 None。"""
        self._ai_service: Optional[IAIService] = None
        self._music_search_service: Optional[IMusicSearchService] = None

    def register_ai_service(self, service: IAIService) -> None:
        """
        註冊 AI 服務的具體實作 (Concrete Implementation)。

        Args:
            service (IAIService): 實作了 IAIService 介面的物件 (例如 GeminiService)。
        """
        self._ai_service = service

    def register_music_search_service(self, service: IMusicSearchService) -> None:
        """
        註冊音樂搜尋服務的具體實作。

        Args:
            service (IMusicSearchService): 實作了 IMusicSearchService 介面的物件。
        """
        self._music_search_service = service

    def register_youtube_service(self, service: IMusicSearchService) -> None:
        """
        [向後相容] 註冊 YouTube 搜尋服務的別名方法。

        為了相容舊版程式碼而保留的方法，實際上等同於呼叫 `register_music_search_service`。

        Args:
            service (IMusicSearchService): 實作了 IMusicSearchService 介面的物件。
        """
        self.register_music_search_service(service)

    @property
    def ai(self) -> IAIService:
        """
        安全取得 AI 服務實例。

        Returns:
            IAIService: 已註冊的 AI 服務實例。

        Raises:
            RuntimeError: 若取用前尚未註冊 AI 服務則拋出錯誤。
        """
        if not self._ai_service:
            raise RuntimeError("AI 服務尚未註冊於容器中。")
        return self._ai_service

    @property
    def youtube(self) -> IMusicSearchService:
        """
        安全取得 YouTube (音樂搜尋) 服務實例。

        Returns:
            IMusicSearchService: 已註冊的音樂搜尋服務實例。

        Raises:
            RuntimeError: 若取用前尚未註冊音樂搜尋服務則拋出錯誤。
        """
        if not self._music_search_service:
            raise RuntimeError("YouTube 搜尋服務尚未註冊於容器中。")
        return self._music_search_service

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        """
        透過字串名稱動態取得服務 (不拋出錯誤)。

        Args:
            name (str): 欲取得的服務名稱 (支援 "ai", "music_search", "youtube")。
            default (Optional[Any], optional): 若找不到服務時的預設回傳值。預設為 None。

        Returns:
            Any: 對應的服務實例，若無則回傳 default 參數設定的值。
        """
        service_map = {
            "ai": self._ai_service,
            "music_search": self._music_search_service,
            "youtube": self._music_search_service,
        }
        return service_map.get(name, default)

    def require(self, name: str) -> Any:
        """
        透過字串名稱動態強制取得服務。

        Args:
            name (str): 欲取得的服務名稱。

        Returns:
            Any: 對應的服務實例。

        Raises:
            RuntimeError: 若指定的服務尚未註冊，則拋出錯誤中斷執行。
        """
        service = self.get(name)
        if service is None:
            raise RuntimeError(f"{name} 服務尚未註冊。")
        return service


def create_service_container() -> ServiceContainer:
    """
    為運作中的應用程式建構並配置具體的服務實例。

    此工廠函式 (Factory Function) 會匯入實際的服務類別 (例如 GeminiService)，
    並將它們註冊到新建立的 ServiceContainer 中。

    Returns:
        ServiceContainer: 已配置完成並準備就緒的服務容器。
    """
    # 延遲匯入以避免潛在的循環依賴 (Circular Dependency) 問題
    from services import GeminiService, YouTubeSearchService

    container = ServiceContainer()
    container.register_ai_service(GeminiService())
    container.register_music_search_service(YouTubeSearchService())
    return container


def require_service(bot: Any, name: str) -> Any:
    """
    通用依賴解析輔助函式。從 Bot 擁有的服務容器或字典中提取指定服務。

    此函式提供了高容錯率的依賴取得方式，相容於物件形式的 `ServiceContainer`
    以及傳統的字典 (`dict`) 形式，供既有較舊的 Cog 或擴充模組無痛過渡使用。

    Args:
        bot (Any): 包含了 `services` 屬性的 Discord 機器人實例。
        name (str): 欲取得的服務名稱。

    Returns:
        Any: 解析出的服務實例。

    Raises:
        RuntimeError: 若 Bot 未掛載 services 屬性，或指定服務不存在時拋出錯誤。
    """
    container = getattr(bot, "services", None)
    if container is None:
        raise RuntimeError("Bot 尚未掛載 services 容器。")

    # 相容傳統字典格式的容器
    if isinstance(container, dict):
        service = container.get(name)
        if service is None:
            raise RuntimeError(f"{name} 服務尚未註冊。")
        return service

    # 優先嘗試呼叫容器本身提供的 require 方法 (相容自訂的 ServiceContainer)
    if hasattr(container, "require"):
        return container.require(name)

    # 備用方案：透過屬性反射取得
    service = getattr(container, name, None)
    if service is None:
        raise RuntimeError(f"{name} 服務尚未註冊。")
    return service
