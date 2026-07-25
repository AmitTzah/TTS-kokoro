# Kokoro TTS GUI

A graphical interface for the Kokoro-82M text-to-speech model, providing an easy way to generate high-quality speech with various voice options.

## Features
- **Instant splash screen** — window appears within milliseconds, with progress feedback during model/voice loading
- Multiple voice options (American/British English, 11 voices)
- Real-time audio generation
- Audio playback controls (play/pause/stop)
- Save generated audio as WAV files
- Automatic model download and setup

## Requirements
- Windows 10/11
- Python 3.8–3.12 (Python 3.13+ is not yet supported by all dependencies)
- eSpeak NG installed at `C:\Program Files\eSpeak NG`
- NVIDIA GPU with CUDA support (optional but recommended)

## Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Download model + voices, run a test
python scripts/setup.py

# 3. Launch the GUI
python -m kokoro_tts
```

Or use the legacy wrapper:
```bash
python tts-gui.pyw
```

## Project Structure

```
TTS-kokoro/
├── pyproject.toml                  # Package metadata + dependencies
├── README.md
├── .gitignore
├── tts-gui.pyw                     # Legacy wrapper (delegates to kokoro_tts)
├── src/
│   └── kokoro_tts/
│       ├── __init__.py
│       ├── __main__.py             # Entry point: python -m kokoro_tts
│       ├── config.py               # Paths, constants, env setup
│       ├── splash.py               # Splash window
│       ├── app.py                  # Controller (orchestrates everything)
│       ├── model/
│       │   └── loader.py           # Model loading
│       ├── voice/
│       │   ├── loader.py           # Voice pack loading
│       │   └── __init__.py         # Voice definitions (re-exports from config)
│       ├── tts/
│       │   └── generator.py        # Audio generation
│       ├── audio/
│       │   ├── player.py           # Pygame playback
│       │   └── saver.py            # WAV save dialog
│       └── ui/
│           ├── main_window.py      # Widget construction
│           └── events.py           # UI state management
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_generator.py
│   ├── test_player.py
│   └── test_voice_loader.py
├── scripts/
│   └── setup.py                    # Model/voice download + test
└── Kokoro-82M/                     # Vendored model (unchanged)
    ├── kokoro.py
    ├── models.py
    ├── istftnet.py
    ├── plbert.py
    ├── config.json
    ├── kokoro-v0_19.pth
    ├── fp16/
    │   └── halve.py
    └── voices/
        └── [11 .pt files]
```

## Installation (Manual)

1. Install eSpeak NG:
   - Download 1.51 64x.msi version from [eSpeak NG releases](https://github.com/espeak-ng/espeak-ng/releases)
   - Install to `C:\Program Files\eSpeak NG`

2. Install Python dependencies:
   ```bash
   pip install torch soundfile pygame phonemizer requests scipy munch transformers
   ```

3. Clone this repository:
   ```bash
   git clone https://github.com/AmitTzah/TTS-kokoro
   cd TTS-kokoro
   ```

4. Run the setup script:
   ```bash
   python scripts/setup.py
   ```

## Usage

Launch the GUI:
```bash
python -m kokoro_tts
```

1. The splash window appears instantly with "Loading Kokoro TTS..."
2. A progress bar shows model and voice loading status
3. Select a voice from the dropdown menu
4. Enter text in the input box
5. Click "Generate Audio" to create speech
6. Use the playback controls to listen
7. Save the audio using the "Save" button

## Voice Options

The GUI provides 11 unique voices:

### American English
- af (Default — 50/50 mix of Bella & Sarah)
- af_bella
- af_nicole
- af_sarah
- af_sky
- am_adam
- am_michael

### British English
- bf_emma
- bf_isabella
- bm_george
- bm_lewis

## Development

Run the test suite:
```bash
python -m pytest tests/ -v
```

## Troubleshooting

### pip Not Found on Windows
If `pip` is not recognized after installing Python:
- Use `python -m pip` instead (e.g., `python -m pip install torch`)
- Or add `Python312\Scripts\` to your user PATH environment variable

### eSpeak NG Installation
- Ensure eSpeak NG is installed at `C:\Program Files\eSpeak NG`
- Verify the following files exist:
  - `C:\Program Files\eSpeak NG\libespeak-ng.dll`
  - `C:\Program Files\eSpeak NG\espeak-ng.exe`

### Model Download Issues
If model files fail to download:
1. Check your internet connection
2. Try running the setup script again:
   ```bash
   python scripts/setup.py
   ```

### CUDA Support
- If you have an NVIDIA GPU, ensure CUDA is properly installed
- The GUI will automatically use CUDA if available

## License
This project is licensed under the Apache 2.0 License — see the [LICENSE](LICENSE) file for details.

The Kokoro-82M model is licensed under Apache 2.0. eSpeak NG is licensed under GPLv3.
