# music/commands/ask.py - 提供 Gemini 文字提問功能的指令 Mixin
from discord.ext import commands


def split_message(text: str, limit: int = 1900) -> list[str]:
    """將過長的文字切分為符合 Discord 訊息長度限制的區塊。

    Args:
        text (str): 要進行切分的文字內容。
        limit (int): 每個區塊的最大字元數。

    Returns:
        list[str]: 切分後的文字區塊列表。

    Notes:
        由於 Discord 訊息有嚴格的字元限制，此工具會優先嘗試依據換行符號進行切割，
        若無法找到換行符號則強制切割。
    """
    chunks = []
    while len(text) > limit:
        # 優先嘗試在限制範圍內尋找最後一個換行符號
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


class AskCommandMixin:
    """提供 Gemini 文字助理指令的 Mixin 類別。"""

    @commands.command(
        name="ask",
        aliases=["gemini", "ai"],
        help="使用 Gemini 問問題並回覆文字",
    )
    async def ask_command(self, ctx: commands.Context, *, question: str = None) -> None:
        """向 Gemini 提出問題並發送文字回覆。

        Args:
            ctx (commands.Context): Discord 指令呼叫上下文。
            question (str): 使用者在指令後輸入的完整問題內容。

        Returns:
            None.

        Notes:
            此指令僅用於純文字對話，不涉及語音頻道的連接或使用。
        """
        if not question:
            return await ctx.send("請提供要問 Gemini 的問題。\n用法: !ask <問題>")

        # 檢查 AI 服務配置
        if not hasattr(self, "gemini") or not self.gemini.is_configured:
            return await ctx.send("❌ 找不到 GEMINI_API_KEY，請先在 .env 設定。")

        msg = await ctx.send("🤔 Gemini 思考中...")

        try:
            # 呼叫 Gemini 生成回應
            answer = await self.gemini.generate_answer(
                question, getattr(ctx.author, "display_name", None)
            )
        except Exception as e:
            return await msg.edit(content=f"⚠️ Gemini 回答失敗：`{e}`")

        # 處理過長的文字回應
        chunks = split_message(f"**Gemini：**\n{answer}")

        # 編輯初始的 "思考中" 訊息，並發送其餘區塊
        await msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await ctx.send(chunk)
