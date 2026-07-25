<h1 align="center">TTS Studio</h1>

<p align="center">
  Multi-engine desktop GUI for local TTS models on Windows
</p>

<p align="center">
  <a href="https://github.com/AmitTzah/TTS-Studio/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.8–3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey" alt="Platform">
</p>

---

Supports multiple TTS engines: **Kokoro-82M** (54 fixed voices, 9 languages) and **Chatterbox** (default voice + voice cloning, 23+ languages, paralinguistic tags). Switch engines via the Provider dropdown.

## Install

Python 3.8–3.12 and [eSpeak NG](https://github.com/espeak-ng/espeak-ng/releases) at `C:\Program Files\eSpeak NG`.

```bash
git clone https://github.com/AmitTzah/TTS-Studio
cd TTS-Studio
pip install -e .                    # Kokoro engine
pip install chatterbox-tts          # Chatterbox engine (optional)
python scripts/setup.py             # pre-download models (~300MB each)
python -m tts_studio                # launch
```

Or skip setup.py — the GUI downloads models on first use via Manage Models.

For NVIDIA GPU:

```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

## Usage

1. Pick a Provider and Model from the dropdowns
2. Select a voice, type text, click Generate
3. Play, pause, stop, save

Use the **Manage Models** button to download or delete models. Models are stored in `models/` (gitignored).

## Engines

| Engine | Voices | Languages | Size |
|--------|--------|-----------|------|
| Kokoro v1.0 | 54 fixed | 9 | 82M |
| Chatterbox Turbo | Default + cloning | English | 350M |
| Chatterbox Multilingual V3 | Default + cloning | 23+ | 500M |

## Structure

```
TTS-Studio/
├── tts-gui.pyw
├── src/tts_studio/
│   ├── app.py                   ← multi-engine controller
│   ├── engines/                 ← TTSEngine abstraction
│   │   ├── kokoro_engine.py
│   │   └── chatterbox_engine.py
│   ├── models/                  ← model catalog + downloader
│   ├── tts/generator.py
│   ├── audio/player.py, saver.py
│   └── ui/                      ← main window, model manager, events
├── tests/                       ← 11 tests
├── models/                      ← gitignored
└── pyproject.toml
```

## Dev

```bash
python -m pytest tests/ -v
```

## License

Apache 2.0.
