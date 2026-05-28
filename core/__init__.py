# core/__init__.py - 標記 core 套件為系統基礎設施層
"""
此模組為 `core` 套件的初始化檔案，將其標記為一個標準的 Python 套件。

此套件作為整個專案的「基礎設施層 (Infrastructure Layer)」，封裝了不包含
Discord 業務邏輯的系統級服務。這裡的程式碼模組化程度高，與業務邏輯完全解耦，
提供了專案運行所需的關鍵支援與共用環境設定。

包含的服務：
- `bot`: 自訂 Discord Bot 與 extension 載入流程。
- `config`: 環境變數設定載入。
- `container`: 應用程式服務容器與依賴解析。
- `logger`: 處理全域日誌系統的初始化、檔案輪轉 (Rotation) 與日誌格式化。
"""
