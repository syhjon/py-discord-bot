# cogs/music.py - 音樂播放的主要 Cog，負責註冊指令和管理播放器
from music.cog import Music

async def setup(bot):
    await bot.add_cog(Music(bot))
