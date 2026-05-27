# Py-Discord-Bot 🎵

A feature-rich Discord music and AI voice assistant bot built with Python (`discord.py`). It features comprehensive playback controls, personalized playlist management, and AI-driven interactive capabilities.

## ✨ Key Features
* 🎶 **Playback Controls**: Supports YouTube search, direct URL playback, seeking, queue management, and loop play.
* 💾 **Personalized Playlists**: Save your current queue as a custom playlist (`!saveplaylist`) and load it seamlessly anytime.
* 🤖 **AI Voice Assistant**: Integrated with the Gemini API for conversational and music-related voice interactions.
* 🛡️ **Highly Reliable Architecture**: Utilizes the Mixin design pattern for modular, maintainable, and highly extensible code, avoiding the "God Object" anti-pattern.
* 📊 **Professional Monitoring**: Built-in system logging (`core/logger.py`) with automatic file rotation and size management.

## ⚙️ System Requirements
* Python 3.10+
* FFmpeg (Required for audio stream processing)

## 🚀 Quick Start
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment Variables**:
Create a .env file in the root directory and add your Discord Token:
   ```bash
   DISCORD_TOKEN=your_bot_token_here

1. **Run the Bot**:
   ```bash
   python main.py
   ```

## 📂 Directory Structure
.
├── cogs/            # Core commands and Cog extension modules
├── core/            # System-level core services (Logging, Config)
├── music/           # Music playback core logic (Player, UI, Services)
├── logs/            # System execution logs (Auto-generated)
├── playlists/       # User playlist storage (Auto-generated)
└── main.py          # Application entry point

## 📄 License
MIT License.