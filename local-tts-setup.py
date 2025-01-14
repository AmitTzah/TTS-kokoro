import os
import requests
from pathlib import Path
import sys

# Add Kokoro-82M directory to Python path
KOKORO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Kokoro-82M')
sys.path.append(KOKORO_DIR)

def configure_espeak():
    """Configure espeak-ng paths for Windows"""
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
    os.environ["PHONEMIZER_ESPEAK_PATH"] = r"C:\Program Files\eSpeak NG\espeak-ng.exe"
    
    print("PHONEMIZER_ESPEAK_LIBRARY:", os.environ.get("PHONEMIZER_ESPEAK_LIBRARY"))
    print("PHONEMIZER_ESPEAK_PATH:", os.environ.get("PHONEMIZER_ESPEAK_PATH"))
    
    if not os.path.exists(os.environ["PHONEMIZER_ESPEAK_LIBRARY"]):
        raise FileNotFoundError(f"Could not find espeak library at {os.environ['PHONEMIZER_ESPEAK_LIBRARY']}")
    if not os.path.exists(os.environ["PHONEMIZER_ESPEAK_PATH"]):
        raise FileNotFoundError(f"Could not find espeak executable at {os.environ['PHONEMIZER_ESPEAK_PATH']}")

def download_model(filename):
    """Download model file if it doesn't exist"""
    full_path = os.path.join(KOKORO_DIR, filename)
    if not os.path.exists(full_path):
        print(f"Model file {filename} not found. Attempting to download...")
        url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/{filename}"
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                
        print(f"Downloaded {filename} successfully!")
    return full_path

# Configure espeak BEFORE importing any other modules
configure_espeak()

# Now import the rest of the modules
import torch
from models import build_model
from kokoro import generate
import soundfile as sf

def setup_tts():
    # Check if CUDA is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Ensure model file exists and get its path
    model_file = download_model('kokoro-v0_19.pth')
    
    # Build the model
    model = build_model(model_file, device)
    
    # Load voice pack
    voice_name = 'af'  # Default voice (50-50 mix of Bella & Sarah)
    
    #download all the voices
    names = [
    "af.pt",
    "af_bella.pt",
    "af_nicole.pt",
    "af_sarah.pt",
    "af_sky.pt",
    "am_adam.pt",
    "am_michael.pt",
    "bf_emma.pt",
    "bf_isabella.pt",
    "bm_george.pt",
    "bm_lewis.pt"
]
    

   
    for name in names:
        voice_file = download_model(f'voices/{name}')
    
    voicepack = torch.load(voice_file, weights_only=True).to(device)
    print(f'Loaded voice: {voice_name}')
    
    return model, voicepack, voice_name

def generate_speech(model, voicepack, text, voice_name, output_file="output.wav"):
    # Generate audio
    audio, phonemes = generate(model, text, voicepack, lang=voice_name[0])
    
    # Save audio to file using absolute path
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    sf.write(output_path, audio, 24000)
    print(f"Audio saved to {output_path}")
    print(f"Phonemes: {phonemes}")

def main():
    # Example text
    text = "How could I know? It's an unanswerable question. Like asking an unborn child if they'll lead a good life. They haven't even been born."
    
    # Setup model and voice
    model, voicepack, voice_name = setup_tts()
    
    # Generate speech
    generate_speech(model, voicepack, text, voice_name)

if __name__ == "__main__":
    main()