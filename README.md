<h1 align="center">TTS Studio</h1>

<p align="center">
  Desktop GUI for local text-to-speech models on Windows
  <br>
  Currently powered by <a href="https://huggingface.co/hexgrad/Kokoro-82M">Kokoro-82M</a> v1.0
</p>

<p align="center">
  <a href="https://github.com/AmitTzah/TTS-kokoro/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.8–3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey" alt="Platform">
</p>

---

Type or paste text, pick a voice, generate audio. All local.

## Install

You need Python 3.8–3.12 and [eSpeak NG](https://github.com/espeak-ng/espeak-ng/releases) at `C:\Program Files\eSpeak NG`.

```bash
git clone https://github.com/AmitTzah/TTS-Studio
cd TTS-Studio
pip install -e .
python scripts/setup.py        # downloads model (~300MB) + tests
python -m kokoro_tts            # launch
```

Or double-click `tts-gui.pyw`.

For NVIDIA GPU:

```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

## Usage

1. Launch, wait for model to load
2. Pick a voice
3. Type text, click Generate
4. Play, pause, stop, save

## Voices

54+ voices across 9 languages. The voice list is fetched from Hugging Face at startup.

| Language | Code | Examples |
|----------|------|----------|
| American English | `a` | `af_heart`, `af_bella`, `am_adam` |
| British English | `b` | `bf_emma`, `bf_isabella`, `bm_george` |
| Japanese | `j` | `jf_alpha`, `jm_alpha` |
| Mandarin Chinese | `z` | `zf_alpha`, `zm_alpha` |
| Spanish, French, Hindi, Italian, Portuguese | `e`, `f`, `h`, `i`, `p` | espeak-ng voices |

## Structure

```
TTS-kokoro/
├── tts-gui.pyw
├── src/kokoro_tts/
│   ├── __main__.py          ← entry point
│   ├── app.py               ← controller
│   ├── config.py            ← paths, languages, HF_HOME
│   ├── splash.py            ← splash window
│   ├── tts/generator.py     ← audio generation
│   ├── audio/player.py      ← playback
│   ├── audio/saver.py       ← WAV export
│   └── ui/                  ← tkinter widgets + state
├── scripts/setup.py         ← install + version check
├── tests/                   ← 9 tests
└── models/                  ← gitignored, model weights
```

## How it works

Uses the [`kokoro`](https://pypi.org/project/kokoro/) pip package. `KPipeline` handles G2P, chunking, voice loading, and model download. Weights go into `models/huggingface/` (gitignored). Generation runs on a background thread.

## Dev

```bash
python -m pytest tests/ -v
python scripts/setup.py      # also checks for model updates
```

## Troubleshooting

**eSpeak not found**: must be `C:\Program Files\eSpeak NG\libespeak-ng.dll`.

**Model on cpu**: you have CPU PyTorch. Reinstall with CUDA (see above).

**Download fails**: delete `models/huggingface/` to retry.

## License

Apache 2.0.
