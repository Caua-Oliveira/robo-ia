import json
import re
import sys
import time
import google.generativeai as genai
import speech_recognition as sr

from config import rec, MODEL_NAME
from audio import speech_to_text, text_to_speech
from queries import build_system_instruction
from tools import get_locais, get_coordenacao, AVAILABLE_TOOLS

# ===== Customization knobs =====
PHRASE_TIME_LIMIT = 12
PAUSE_THRESHOLD = 1.3
NON_SPEAKING_DURATION = 0.9
USE_ACTIVATION_PHRASE = True
ACTIVATION_REGEX = re.compile(r'^\s*(?:e(?:\s*a[ií]|i)\s+cleiton|cleiton)\b[\s,]*', re.IGNORECASE)

CHAT_HISTORY = []
USER_QUESTIONS = []
chat_session = None


def start_chat():
    global chat_session

    system_instruction = build_system_instruction()
    rec.pause_threshold = PAUSE_THRESHOLD
    rec.non_speaking_duration = NON_SPEAKING_DURATION

    # Informa ao modelo quais ferramentas ele pode usar
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
        tools=[get_locais, get_coordenacao]
    )
    chat_session = model.start_chat(history=[])

    print("Cleiton online.")

    with sr.Microphone() as mic:
        rec.adjust_for_ambient_noise(mic)
        while True:
            try:
                text = listen_and_return_text(mic)
                if not text: continue

                if "cleiton sair" in text.lower():
                    text_to_speech("Encerrando. Até logo!")
                    sys.exit()

                question = extract_question(text)
                if not question: continue

                register_and_print_question(question)
                response = generate_prompt(question)
                if response:
                    text_to_speech(response)

            except sr.WaitTimeoutError:
                pass
            except KeyboardInterrupt:
                print("Encerrando...")
                break
            except Exception as e:
                print(f"Erro inesperado: {e}")


def listen_and_return_text(mic: sr.Microphone) -> str:
    print("Ouvindo...")
    audio = rec.listen(mic, timeout=5, phrase_time_limit=PHRASE_TIME_LIMIT)
    print("Processando...")
    return speech_to_text(audio)


def extract_question(text: str) -> str:
    if not USE_ACTIVATION_PHRASE:
        return text.strip()
    m = ACTIVATION_REGEX.match(text)
    if not m: return ""
    return text[m.end():].strip() or "Olá" # Se só disse "cleiton", troca por "Olá"


def register_and_print_question(question: str):
    USER_QUESTIONS.append(question)
    print(f"Pergunta #{len(USER_QUESTIONS)}: {question}")


def generate_prompt(user_question: str) -> str:
    global chat_session
    if not chat_session:
        raise RuntimeError("Sessão Gemini não inicializada.")

    print(f"Enviando ao LLM: {user_question}")
    print("Pensando...")

    try:
        # 1. Envia a mensagem do usuário
        response = chat_session.send_message(user_question)

        # 2. Verifica se a IA solicitou uma ferramenta
        function_call = response.candidates[0].content.parts[0].function_call
        if not function_call:
            return (response.text or "").strip()

        # 3. Executa a ferramenta solicitada
        tool_name = function_call.name
        if tool_name in AVAILABLE_TOOLS:
            print(f"IA solicitou a ferramenta: {tool_name}")
            tool_function = AVAILABLE_TOOLS[tool_name]
            tool_result = tool_function()

            # 4. Envia o resultado da ferramenta de volta para a IA
            function_response_part = {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": tool_result},
                }
            }
            response = chat_session.send_message(function_response_part)
            return (response.text or "").strip()
        else:
            return f"Erro: Ferramenta '{tool_name}' não encontrada."

    except Exception as e:
        print(f"Erro ao gerar resposta: {e}")
        return "Desculpe, tive um problema ao processar sua pergunta."


if __name__ == "__main__":
    start_chat()