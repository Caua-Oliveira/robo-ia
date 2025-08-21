import json
import re
import sys
import time
import unicodedata
from pathlib import Path
import google.generativeai as genai
import speech_recognition as sr

from util import transform_group
from config import rec, MODEL_NAME
from message import Message
from audio import speech_to_text, text_to_speech
from queries import build_system_instruction

# ===== Customization knobs =====
PHRASE_TIME_LIMIT = 12        # Max seconds to record each question
PAUSE_THRESHOLD = 1.3         # Silence length that ends the question
NON_SPEAKING_DURATION = 0.7   # Allowed start/end silence padding
#MAX_TOTAL_CAPTURE = 5
#MAX_INTER_SILENCE = 1.5

# If you want to REMOVE the activation phrase completely, set this to False
USE_ACTIVATION_PHRASE = True
# Matches: "cleiton" OR "e ai cleiton" / "e aí cleiton"
ACTIVATION_REGEX = re.compile(
    r'^\s*(?:e(?:\s*a[ií]|i)\s+cleiton|cleiton)\b[\s,]*',
    re.IGNORECASE
)

CHAT_HISTORY = []
USER_QUESTIONS = []
chat_session = None
CLASSES_DATA = []  # loaded from local JSON


def load_classes():
    global CLASSES_DATA
    data_path = Path(__file__).parent / "data" / "classes.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            CLASSES_DATA = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar classes locais: {e}")
        CLASSES_DATA = []


def build_schedule_summary() -> str:
    if not CLASSES_DATA:
        return "Nenhuma aula carregada."
    lines = []

    for c in CLASSES_DATA:
        turma_letra = transform_group(c.get("turma"))
        dia = c.get("dayOfWeek", "").capitalize()
        hora = c.get("timeIn", "")
        prof = c.get("professorName", "")
        sala = c.get("roomNumber", "")
        andar = c.get("roomFloor", "")
        materia = c.get("subjectName", "")
        lines.append(
            f"- {dia}: {hora} - {materia} (Prof. {prof}), Turma {turma_letra}, Sala {sala}, Andar {andar}"
        )
    return "\n".join(lines)


def start_chat():
    global chat_session

    load_classes()

    rec.pause_threshold = PAUSE_THRESHOLD
    rec.non_speaking_duration = NON_SPEAKING_DURATION

    schedule_summary = build_schedule_summary()
    system_instruction = build_system_instruction(schedule_summary)

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction
    )
    chat_session = model.start_chat(history=[])

    CHAT_HISTORY.append({"role": "system", "content": system_instruction})

    print("Cleiton online (modo respostas naturais).")

    with sr.Microphone() as mic:
        rec.adjust_for_ambient_noise(mic)
        while True:
            try:
                text = listen_and_return_text(mic)
                if not text:
                    continue

                # If you still want a voice command to exit:
                if "cleiton sair" in text.lower():
                    text_to_speech("Encerrando. Até logo!")
                    sys.exit()

                question = extract_question(text)
                if not question:
                    continue

                register_and_print_question(question)
                response = generate_prompt(question)
                if response:
                    text_to_speech(response, 1.0)

            except sr.WaitTimeoutError:
                pass
            except KeyboardInterrupt:
                print("Encerrando...")
                break
            except Exception as e:
                print(f"Erro inesperado: {e}")


def listen_and_return_text(mic: sr.Microphone) -> str:
    print("Ouvindo...")
    audio = rec.listen(
        mic,
        timeout=5,
        phrase_time_limit=PHRASE_TIME_LIMIT
    )
    print("Processando...")
    return speech_to_text(audio)


def extract_question(text: str) -> str:
    if not USE_ACTIVATION_PHRASE:
        return text.strip()
    m = ACTIVATION_REGEX.match(text)
    if not m:
        return ""
    return text[m.end():].strip() or "Olá"


def register_and_print_question(question: str):
    USER_QUESTIONS.append(question)
    print(f"Pergunta #{len(USER_QUESTIONS)}: {question}")


def generate_prompt(user_question: str) -> str:
    global chat_session
    if not chat_session:
        raise RuntimeError("Sessão Gemini não inicializada.")
    print(f"Enviando ao LLM: {user_question}")
    user_msg = Message(role="user", content=user_question)
    CHAT_HISTORY.append(user_msg.full_message())
    print("Pensando...")
    response = chat_session.send_message(user_question)
    answer_text = response.text or ""
    assistant_msg = Message(role="assistant", content=answer_text)
    CHAT_HISTORY.append(assistant_msg.full_message())
    return answer_text.strip()


if __name__ == "__main__":
    start_chat()