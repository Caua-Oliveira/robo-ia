import sys
import re
import pyaudio
import webrtcvad
from config import *
from audio import speech_to_text, text_to_speech, text_to_speech_genai
from queries import build_system_instruction
from tools import get_locais, get_coordenacao, AVAILABLE_TOOLS

# Regex para detectar a frase de ativação "Ei Cleiton" ou "Cleiton"
USE_ACTIVATION_PHRASE = True
ACTIVATION_REGEX = re.compile(r'^\s*(?:e(?:\s*a[ií]|i)\s|jorgina|georgina|regina|vagina )\b[\s,]*', re.IGNORECASE)

USER_QUESTIONS = []
chat_session = None
MAX_USER_TURNS = 2


def listen_with_vad() -> sr.AudioData | None:
    """
    Escuta a fala usando VAD e retorna um objeto AudioData para transcrição.
    """
    p = pyaudio.PyAudio()
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=VAD_SAMPLE_RATE,
        input=True,
        frames_per_buffer=VAD_CHUNK_SIZE
    )

    print("Ouvindo...")
    started = False
    speech_frames = []
    silent_chunks = 0

    while True:
        audio_chunk = stream.read(VAD_CHUNK_SIZE)
        is_speech = vad.is_speech(audio_chunk, VAD_SAMPLE_RATE)

        if not started and is_speech:
            print("Fala detectada, gravando...")
            started = True
            speech_frames.append(audio_chunk)
        elif started and is_speech:
            speech_frames.append(audio_chunk)
            silent_chunks = 0
        elif started and not is_speech:
            silent_chunks += 1
            speech_frames.append(audio_chunk)
            if silent_chunks > VAD_PADDING_CHUNKS:
                print("Silêncio detectado, processando...")
                break

    stream.stop_stream()
    stream.close()
    p.terminate()

    if not speech_frames:
        return None

    audio_data_bytes = b''.join(speech_frames)
    return sr.AudioData(
        frame_data=audio_data_bytes,
        sample_rate=VAD_SAMPLE_RATE,
        sample_width=2
    )


def start_chat_vad():
    global chat_session

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=build_system_instruction(),
        tools=[get_locais, get_coordenacao]
    )
    chat_session = model.start_chat(history=[])
    print("Jorgina online.")

    while True:
        try:
            audio_data = listen_with_vad()
            if not audio_data:
                continue

            text = speech_to_text(audio_data)
            if not text:
                continue

            if "jorgina sair" in text.lower():
                text_to_speech("Encerrando. Até logo!")
                sys.exit()
            print(text)
            question = extract_question(text)
            if not question:
                continue

            register_and_print_question(question)
            response = generate_prompt(question)
            if response:
                text_to_speech(response)

        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"Erro inesperado no loop principal: {e}")


def extract_question(text: str) -> str:
    if not USE_ACTIVATION_PHRASE:
        return text.strip()
    m = ACTIVATION_REGEX.match(text)
    if not m: return ""
    return text[m.end():].strip() or "Olá"


def register_and_print_question(question: str):
    USER_QUESTIONS.append(question)
    if len(USER_QUESTIONS) > 3:
        USER_QUESTIONS.pop(0)
    print(f"Pergunta #{len(USER_QUESTIONS)}: {question}")


def generate_prompt(user_question: str) -> str:
    global chat_session
    if not chat_session:
        raise RuntimeError("Sessão Gemini não inicializada.")

    if len(chat_session.history) > MAX_USER_TURNS * 2:
        chat_session.history = []

    print(f"Enviando ao LLM: {user_question}")
    print("Pensando...")
    try:
        response = chat_session.send_message(user_question)

        # Se a resposta não for uma chamada de ferramenta, apenas retorne o texto.
        if not response.candidates[0].content.parts or not response.candidates[0].content.parts[0].function_call:
            return (response.text or "").strip()

        function_call = response.candidates[0].content.parts[0].function_call
        tool_name = function_call.name

        if tool_name in AVAILABLE_TOOLS:
            print(f"IA solicitou a ferramenta: {tool_name}")
            tool_function = AVAILABLE_TOOLS[tool_name]
            tool_result = tool_function()

            function_response_part = {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": tool_result},
                }
            }

            # --- Espera pela resposta da IA ---
            MAX_RETRIES = 6
            for attempt in range(MAX_RETRIES):
                print(f"Enviando resultado da ferramenta para a IA (Tentativa {attempt + 1}/{MAX_RETRIES})...")
                response = chat_session.send_message(function_response_part)

                # Verifica se a resposta recebida é válida e contém texto
                if response.candidates and response.candidates[0].content.parts and hasattr(
                        response.candidates[0].content.parts[0], 'text'):
                    final_text = "".join(
                        part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                    if final_text.strip():
                        return final_text.strip()  # Sucesso, retorna a resposta

                # Se a resposta não for válida, informa e o loop continuará para a próxima tentativa
                print(f"A IA retornou uma resposta vazia. Tentando novamente...")

            # Se o loop terminar sem sucesso após todas as tentativas
            print("A IA não conseguiu gerar uma resposta de texto após várias tentativas.")
            return "Desculpe, não consegui processar a informação. Pode perguntar de novo?"

        else:
            return f"Erro: Ferramenta '{tool_name}' não encontrada."

    except Exception as e:
        print(f"Erro ao gerar resposta: {e}")
        return "Desculpe, tive um problema ao processar sua pergunta."
