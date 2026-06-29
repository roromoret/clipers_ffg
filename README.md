# clipers_ffg

A local desktop application designed to easily convert landscape gaming clips (16:9) into vertical shorts (9:16) for TikTok, YouTube Shorts, and Reels.

## Features

- **Dynamic Layout:** Autocrop and stack gameplay in the center and your webcam at the top.
- **Smart Background:** The remaining top/bottom empty spaces are automatically filled with a blurred version of your gameplay to keep a clean look.
- **Local AI Transcription:** Integrated subtitle generation using Whisper (runs entirely on your machine).
- **Customizable:** Toggle webcam overlay or custom top titles on/off depending on your needs.
- **Persistent Preferences:** Remembers your webcam positioning and checkbox settings every time you reopen the app.

---

## For Users (Quick Start)

You don't need to install Python, libraries, or any external tools to use this software. Everything is packaged and ready to run.

1. Head over to the **[Releases](https://github.com/roromoret/clipers_ffg/releases)** section of this repository.
2. Download the latest `.zip` archive for your system.
3. Extract the folder anywhere on your computer.
4. Double-click `clipers_ffg.exe` to launch the application.

---

## For Developers (Setup & Contribution)

If you want to run the project from source or contribute to the development, follow these steps:

### 1. Prerequisites & FFmpeg Setup
This project relies heavily on **FFmpeg** for video processing. To keep the project portable and independent of system environment variables, you must place the executable directly inside the project root.

1. Download the FFmpeg essentials binaries for your OS (e.g., from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) for Windows).
2. Extract the archive and locate `ffmpeg.exe` (inside the `bin` folder).
3. Copy and paste `ffmpeg.exe` directly into the **root directory** of this project (next to `main.py`).

*Note: `ffmpeg.exe` and `config.json` are already added to `.gitignore` to keep the repository light and clean.*

### 2. Installation
Clone the repository and install the required dependencies:

```bash
git clone git@github.com:roromoret/clipers_ffg.git
cd clipers_ffg

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
