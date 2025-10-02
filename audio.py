from pathlib import Path
from config import *
import pygame
import keyboard
import warnings
from gtts import gTTS
from google import genai
from google.genai import types
import wave


warnings.filterwarnings("ignore", category=DeprecationWarning)

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

def text_to_speech(text):
    print(text)
    try:
        tts = gTTS(text=text, lang='pt', tld='com.br')
        tts.save(str(AUDIO_FILE_PATH))
        play_audio(AUDIO_FILE_PATH)
    except Exception as e:
        print(f"Erro na conversão de texto para fala: {e}")


# Helper para o TTS do Genai
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def text_to_speech_genai(text):
    print(text)
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents="Fale isso em um sotaque baiano leve: " + text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                    )
                )
            ),
        )
    )

    data = response.candidates[0].content.parts[0].inline_data.data

    file_name = 'out.wav'
    wave_file(file_name, data)
    play_audio(file_name)