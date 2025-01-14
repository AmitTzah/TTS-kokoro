# Kokoro TTS GUI

A graphical interface for the Kokoro-82M text-to-speech model, providing an easy way to generate high-quality speech with various voice options.

## Features
- Multiple voice options (American/British English)
- Real-time audio generation
- Audio playback controls (play/pause/stop)
- Save generated audio as WAV files
- Progress indicators during generation
- Automatic model download and setup

## Requirements
- Windows 10/11
- Python 3.8+
- eSpeak NG installed at `C:\Program Files\eSpeak NG`
- NVIDIA GPU with CUDA support (optional but recommended)

## Installation

1. Install eSpeak NG:
   - Download 1.51 64x.msi version from [eSpeak NG releases](https://github.com/espeak-ng/espeak-ng/releases)
   - Install to `C:\Program Files\eSpeak NG`

2. Install Python dependencies:
   ```bash
   pip install torch soundfile pygame phonemizer
   ```

3. Clone this repository:
   ```bash
   git clone https://github.com/AmitTzah/TTS-kokoro
   cd tts-gui
   ```

4. Run the setup script:
   ```bash
   python local-tts-setup.py
   ```

## Usage

1. Launch the GUI:
   ```bash
   python tts-gui.pyw
   ```

2. Select a voice from the dropdown menu

3. Enter text in the input box

4. Click "Generate Audio" to create speech

5. Use the playback controls to listen to the generated audio

6. Save the audio using the "Save" button

## Voice Options

The GUI provides 10 unique voices:

### American English
- af (Default - 50/50 mix of Bella & Sarah)
- af_bella
- af_nicole  
- af_sarah
- af_sky

### British English
- bf_emma
- bf_isabella
- bm_george
- bm_lewis

## Troubleshooting

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
   python local-tts-setup.py
   ```

### CUDA Support
- If you have an NVIDIA GPU, ensure CUDA is properly installed
- The GUI will automatically use CUDA if available

## License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

The Kokoro-82M model is licensed under Apache 2.0. eSpeak NG is licensed under GPLv3.
