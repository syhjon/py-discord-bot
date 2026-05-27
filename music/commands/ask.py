from discord.ext import commands


def split_message(text, limit=1900):
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


class AskCommandMixin:
    @commands.command(
        name="ask",
        aliases=["gemini", "ai"],
        help="使用 Gemini 問問題並回覆文字",
    )
    async def ask_command(self, ctx, *, question: str = None):
        if not question:
            return await ctx.send("請提供要問 Gemini 的問題。\n用法: !ask <問題>")
        if not self.gemini.is_configured:
            return await ctx.send("❌ 找不到 GEMINI_API_KEY，請先在 .env 設定。")

        msg = await ctx.send("🤔 Gemini 思考中...")
        try:
            answer = await self.gemini.generate_answer(
                question, getattr(ctx.author, "display_name", None)
            )
        except Exception as e:
            return await msg.edit(content=f"⚠️ Gemini 回答失敗：`{e}`")

        chunks = split_message(f"**Gemini：**\n{answer}")
        await msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await ctx.send(chunk)
