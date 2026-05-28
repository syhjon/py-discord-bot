# assistant/services/ask.py - 處理與 Gemini AI 助理互動的服務邏輯
"""
Gemini AI 助理的服務邏輯層 (Services Layer)。

此模組包含了與 Gemini AI 進行文字問答互動的核心商業邏輯。
負責處理 Discord 訊息長度限制的分段、提示詞 (Prompt) 的建構，
以及呼叫底層 AI 服務並將結果回傳給使用者的完整流程。
"""

from core.context import InteractionContext
from domain import IAIService

# 定義 Gemini 助理的系統提示詞 (System Prompt) / 人設 (Persona)
ASSISTANT_PROMPT = (
    "你是 Discord 機器人的 AI 助手。\n"
    "請用繁體中文回答，語氣自然、清楚、友善。\n"
    "可以使用簡單 Markdown，但避免表格，盡量控制在 800 字以內。"
)


def split_message(text: str, limit: int = 1900) -> list[str]:
    """
    將過長的文字訊息分割成多個符合 Discord 長度限制的區塊。

    Discord 的單一訊息長度上限為 2000 字元。此函式預設以 1900 字元為界，
    並優先嘗試在換行符號 (`\\n`) 處進行安全分割 (Safe Split)，避免將句子從中截斷。

    Args:
        text (str): 需要被分割的原始長文字。
        limit (int, optional): 單一區塊的字元長度上限。預設為 1900。

    Returns:
        list[str]: 分割後的文字區塊列表。
    """
    chunks = []
    while len(text) > limit:
        # 從字串起點到 limit 範圍內，從右側反向尋找最後一個換行符號
        split_at = text.rfind("\n", 0, limit)

        # 若在該範圍內找不到換行符號（例如超長連續字串），則強制在 limit 處截斷
        if split_at == -1:
            split_at = limit

        # 提取區塊並去除頭尾空白
        chunks.append(text[:split_at].strip())
        # 將剩餘未處理的文字指派回 text 繼續迴圈
        text = text[split_at:].strip()

    # 將最後剩餘的文字加入列表
    if text:
        chunks.append(text)
    return chunks


def build_assistant_prompt(question: str, username: str | None = None) -> str:
    """
    建構發送給 Gemini 的最終提示詞 (Prompt)。

    將系統預設的人設 (Persona) 與發問者的名稱、問題內容進行組合，
    以提供 Gemini 更完整的上下文 (Context)。

    Args:
        question (str): 使用者提出的問題。
        username (str | None, optional): 提出問題的使用者名稱。預設為 None。

    Returns:
        str: 組合完成的完整提示詞字串。
    """
    speaker = f"{username} 問：" if username else "使用者問："
    return f"{ASSISTANT_PROMPT}\n\n{speaker}{question}"


async def ask_gemini(
    ctx: InteractionContext, ai_service: IAIService, question: str | None
) -> None:
    """
    處理使用者向 Gemini 提問的核心非同步服務邏輯。

    此函式涵蓋了完整的問答生命週期：
    1. 輸入驗證 (確保問題存在與 API 金鑰已設定)。
    2. 使用者介面回饋 (發送「思考中...」的等待訊息)。
    3. 建構提示詞並呼叫 AI 服務取得生成結果。
    4. 錯誤處理 (API 呼叫失敗時的回報)。
    5. 訊息後處理與發送 (自動分段過長的回覆)。

    Args:
        ctx (InteractionContext): 封裝了 Discord 互動狀態的上下文物件。
        ai_service (IAIService): 已實作的 AI 服務介面實例。
        question (str | None): 使用者輸入的問題。若為空值則會提早返回並提示。
    """
    # 1. 驗證問題是否為空
    if not question:
        return await ctx.send("請提供要問 Gemini 的問題。\n用法: /ask <問題>")

    # 2. 驗證 AI 服務是否已正確配置 (例如 .env 中的 API Key 是否存在)
    if not ai_service.is_configured:
        return await ctx.send("❌ 找不到 GEMINI_API_KEY，請先在 .env 設定。")

    # 發送初步的等待訊息，告知使用者系統正在處理中
    msg = await ctx.send("🤔 Gemini 思考中...")

    try:
        # 取得發問者的顯示名稱 (Display Name) 作為提示詞的上下文
        prompt = build_assistant_prompt(
            question, getattr(ctx.author, "display_name", None)
        )
        # 呼叫 AI 服務生成文字回覆
        answer = await ai_service.generate_text(prompt)
    except Exception as e:
        # 捕捉任何 API 呼叫期間發生的例外，並編輯原訊息以顯示錯誤
        return await msg.edit(content=f"⚠️ Gemini 回答失敗：`{e}`")

    # 將生成的文字加上前綴，並使用 split_message 處理可能超過 Discord 限制長度的情況
    chunks = split_message(f"**Gemini：**\n{answer}")

    # 將「思考中...」的初始訊息編輯為回覆的第一個區塊
    await msg.edit(content=chunks[0])

    # 若有後續區塊，則以接續發送新訊息的方式呈現
    for chunk in chunks[1:]:
        await ctx.send(chunk)
