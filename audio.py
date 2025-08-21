from pathlib import Path
from config import *
import pygame
import keyboard
import warnings
from gtts import gTTS

# Ignore deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configure audio file path
AUDIO_FILE_PATH = Path(__file__).parent / "audios" / "output.mp3"
OUTPUT_DIR = AUDIO_FILE_PATH.parent
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
if not AUDIO_FILE_PATH.exists():
    AUDIO_FILE_PATH.touch()

def play_audio(file_path):
    pygame.init()
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if keyboard.is_pressed("space"):
                pygame.mixer.music.stop()
                print("\n##### Reprodução interrompida. #####")
                return
    except pygame.error as e:
        print(f"Erro ao reproduzir áudio: {str(e)}")
    finally:
        pygame.quit()

def speech_to_text(audio):
    try:
        text = rec.recognize_google(audio, language=language)
        return text
    except Exception as e:
        print("Falha no reconhecimento de voz " + str(e))
        return ""

def text_to_speech(text, speed=1.0):
    """
    Converte texto em fala usando gTTS.
    Observação: gTTS não suporta ajuste direto de velocidade.
    O parâmetro speed é ignorado aqui, mas mantido para compatibilidade.
    """
    print(text)
    try:
        tts = gTTS(text=text, lang='pt', tld='com.br')
        tts.save(str(AUDIO_FILE_PATH))
        play_audio(AUDIO_FILE_PATH)
    except Exception as e:
        print(f"Erro na conversão de texto para fala: {e}")