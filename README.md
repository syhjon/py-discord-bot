# Py Discord Music Bot

A modular Discord music bot built with Python and `discord.py`.

The bot focuses on YouTube music playback, queue management, personal playlists, and a lightweight Gemini-powered text assistant. The codebase is split into small command, UI, service, and player modules so each command can be maintained independently instead of living in one large Cog file.

## Features

- **YouTube music playback**: Search YouTube, play direct URLs, or quickly play the top search result.
- **Queue controls**: View the queue, remove tracks, clear the queue, shuffle, skip, jump to a queue position, or play a previous track.
- **Playback controls**: Pause, resume, stop, seek, loop a song, or loop the queue.
- **Volume controls**: Set volume directly, increase/decrease volume, mute, unmute, and check the current volume.
- **Personal playlists**: Save the current queue to a per-user JSON playlist and load it later.
- **Now playing views**: Show the current track with a text progress bar.
- **Lyrics lookup**: Search lyrics for the currently playing song.
- **Gemini text assistant**: Ask Gemini questions with `!ask`, `!gemini`, or `!ai`. Responses are text-only.
- **Structured logging**: Console and rotating file logs are handled through `core/logger.py`.
- **Modular command layout**: Each command lives in its own file under `music/commands/`.

## Requirements

- Python 3.10 or newer
- FFmpeg installed and available in your system `PATH`
- A Discord bot token
- A Gemini API key if you want to use the `!ask` command

On macOS, FFmpeg can be installed with Homebrew:

```bash
brew install ffmpeg
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the Python dependencies:

   ```bash
   python3 -m pip install -U discord.py[voice] yt-dlp python-dotenv watchdog google-genai
   ```

3. Create a `.env` file in the project root:

   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   `DISCORD_TOKEN` is required to run the bot. `GEMINI_API_KEY` is only required for Gemini text responses.

4. Enable the required Discord developer portal settings:

   - Turn on the **Message Content Intent** for your bot.
   - Invite the bot with permissions for reading messages, sending messages, connecting to voice channels, and speaking in voice channels.

## Running The Bot

Run the bot directly:

```bash
python3 main.py
```

Or use the included development script, which restarts the bot whenever Python files change:

```bash
./run.sh
```

Stop the bot with `Ctrl+C`. The application catches the interrupt and shuts down without printing a long traceback.

## Command Overview

The default command prefix is `!`.

### Music Search And Playback

- `!song <query or url>`: Search YouTube and choose a result from a dropdown menu.
- `!quick <query or url>` / `!fast` / `!play`: Play the most relevant result immediately.
- `!cutin <query or url>` / `!insert` / `!插播` / `!pn`: Insert a track at the front and play it next.

### Playback Controls

- `!pause`: Pause the current track.
- `!resume`: Resume playback.
- `!stop` / `!leave` / `!停止`: Stop playback and disconnect from voice.
- `!skip` / `!next` / `!跳過`: Skip the current track.
- `!previous`: Play the previous track from history.
- `!seek <seconds>`: Seek to a time position in the current track.

### Queue Controls

- `!queue` / `!list`: Show the current queue.
- `!clear` / `!clearqueue`: Clear the queue.
- `!remove <index>` / `!rm` / `!刪除`: Remove a track from the queue.
- `!shuffle` / `!random` / `!mix`: Shuffle the queue.
- `!jump <index>`: Move a queued track to the front and play it next.
- `!playat <index>` / `!pt`: Same behavior as `!jump`.

### Loop And Volume

- `!loop off`: Disable looping.
- `!loop song`: Loop the current song.
- `!loop queue` or `!loop all`: Loop the full queue.
- `!volume <0-100>`: Set volume.
- `!volup`: Increase volume by 10%.
- `!voldown`: Decrease volume by 10%.
- `!volumecheck` / `!vol`: Show current volume.
- `!mute`: Mute the bot.
- `!unmute`: Restore the previous volume.

### Status, Playlists, And AI

- `!nowplaying` / `!np` / `!now`: Show the currently playing track.
- `!progress`: Show playback progress.
- `!lyrics` / `!ly`: Search lyrics for the current song.
- `!saveplaylist <name>` / `!sl`: Save the current track and queue as a playlist.
- `!playplaylist <name>` / `!ppl`: Load a saved playlist into the queue.
- `!ask <question>` / `!gemini` / `!ai`: Ask Gemini a question and receive a text response.
- `!help` / `!commands` / `!h` / `!指令` / `!教學`: Show the command list.

## Directory Structure

```text
py-discord-bot/
├── cogs/
│   └── music.py                 # Thin discord.py extension entry point
├── core/
│   ├── __init__.py
│   └── logger.py                # Console and rotating file logging
├── logs/                        # Generated runtime logs; ignored by Git
├── music/
│   ├── commands/                # One command mixin per file
│   │   ├── ask.py               # Gemini text assistant command
│   │   ├── clear.py
│   │   ├── cutin.py
│   │   ├── help.py
│   │   ├── nowplaying.py
│   │   ├── playplaylist.py
│   │   ├── queue.py
│   │   ├── quick.py
│   │   ├── saveplaylist.py
│   │   ├── song.py
│   │   └── ...                  # Other playback, queue, loop, and volume commands
│   ├── services/
│   │   ├── gemini.py            # Gemini text generation service
│   │   ├── playlists.py         # Playlist storage helpers
│   │   └── youtube.py           # yt-dlp search/extraction helpers
│   ├── ui/
│   │   ├── controls.py          # Playback control buttons
│   │   ├── help.py              # Paginated help view
│   │   └── song_select.py       # Search result dropdown
│   ├── utils/
│   │   └── time.py              # Time formatting and progress bar helpers
│   ├── cog.py                   # Main Music Cog composed from command mixins
│   └── player.py                # Queue state, voice playback, loops, seeking
├── playlists/                   # Generated per-user playlist JSON files; ignored by Git
├── .env                         # Local secrets; ignored by Git
├── .gitignore
├── main.py                      # Application entry point
├── README.md
└── run.sh                       # Development auto-restart runner
```

## Adding Or Removing Commands

To add a new command:

1. Create a new file in `music/commands/`, for example `ping.py`.
2. Define a mixin class with a `@commands.command(...)` method.
3. Export that mixin in `music/commands/__init__.py`.
4. Add the mixin to the `Music` class inheritance list in `music/cog.py`.

To remove a command, reverse those steps: remove the mixin from `music/cog.py`, remove the export from `music/commands/__init__.py`, then delete the command file if it is no longer needed.

## Generated Files

The following paths are generated at runtime and should not be committed:

- `.env`: Local environment variables and secrets.
- `logs/`: Rotating bot log files.
- `playlists/`: Per-user playlist JSON files.
- `venv/` and `.venv/`: Local virtual environments.

## License

MIT License.
