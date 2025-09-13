import speech_recognition as sr
import google.generativeai as genai


GEMINI_API_KEY = "AIzaSyAegDM89dCDTPw5Io07nOoowKr9TaYWXw4"
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"

rec = sr.Recognizer() # Reconhecedor de fala
language = 'pt-BR' # Idioma para reconhecimento de fala

# Configurações do VAD (Voice Activity Detection)
VAD_SAMPLE_RATE = 16000  #16kHz
VAD_CHUNK_DURATION_MS = 30  # Duração do chunk em milissegundos
VAD_CHUNK_SIZE = int(VAD_SAMPLE_RATE * VAD_CHUNK_DURATION_MS / 1000)
VAD_AGGRESSIVENESS = 3  # Nível de agressividade do VAD (0-3)
VAD_SILENCE_S = 1.0 # Segundos de silêncio para considerar o fim da fala
VAD_PADDING_CHUNKS = int(VAD_SILENCE_S * 1000 / VAD_CHUNK_DURATION_MS)