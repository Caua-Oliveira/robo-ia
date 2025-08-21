import json
import re
import sys
import unicodedata
from pathlib import Path
import argparse
import google.generativeai as genai

from util import transform_group
from config import MODEL_NAME
from message import Message
from queries import build_system_instruction

# ============ Activation / behavior knobs (voice removed) ============
USE_ACTIVATION_PHRASE = True
# Matches: "cleiton" OR "e ai cleiton" / "e aí cleiton" (with accent variants), case-insensitive
ACTIVATION_REGEX = re.compile(r'^\s*(e\s*a[ií]\s+cleiton|cleiton)\b[\s,]*', re.IGNORECASE)

CHAT_HISTORY = []
USER_QUESTIONS = []
chat_session = None
CLASSES_DATA = []  # loaded from local JSON


def load_classes():
    """Load local classes JSON into CLASSES_DATA."""
    global CLASSES_DATA
    data_path = Path(__file__).parent / "data" / "classes.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            CLASSES_DATA = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar classes locais: {e}")
        CLASSES_DATA = []


def build_schedule_summary() -> str:
    """
    Transform classes.json into a concise schedule summary
    injected into the system prompt so the LLM can answer naturally.
    """
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


def init_chat():
    """Initialize Gemini chat session with schedule context."""
    global chat_session
    load_classes()
    schedule_summary = build_schedule_summary()
    system_instruction = build_system_instruction(schedule_summary)

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction
    )
    chat_session = model.start_chat(history=[])

    CHAT_HISTORY.append({"role": "system", "content": system_instruction})
    print("Cleiton online (modo texto). Digite sua pergunta.")
    if USE_ACTIVATION_PHRASE:
        print("Use 'cleiton' ou 'e ai cleiton' no início para ativar. (Ex: 'cleiton qual minha próxima aula?')")
    else:
        print("Ativação desabilitada; basta digitar a pergunta diretamente.")
    print("Digite 'sair' ou 'exit' para encerrar.")


def extract_question(text: str) -> str:
    """
    If activation phrase usage is enabled, require it; otherwise return full text.
    Returns empty string if activation required but not found.
    """
    if not USE_ACTIVATION_PHRASE:
        return text.strip()
    m = ACTIVATION_REGEX.match(text)
    if not m:
        return ""
    return text[m.end():].strip() or "Olá"


def register_and_print_question(question: str):
    USER_QUESTIONS.append(question)
    print(f"[Pergunta #{len(USER_QUESTIONS)}] {question}")


def generate_prompt(user_question: str) -> str:
    global chat_session
    if not chat_session:
        raise RuntimeError("Sessão Gemini não inicializada.")
    user_msg = Message(role="user", content=user_question)
    CHAT_HISTORY.append(user_msg.full_message())
    try:
        response = chat_session.send_message(user_question)
        answer_text = (response.text or "").strip()
    except Exception as e:
        answer_text = f"Erro ao gerar resposta: {e}"
    assistant_msg = Message(role="assistant", content=answer_text)
    CHAT_HISTORY.append(assistant_msg.full_message())
    return answer_text


def repl():
    """Simple synchronous input() loop replacing voice input."""
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando. Até logo!")
            break

        if not raw:
            continue

        low = raw.lower()
        if low in ("sair", "exit", "quit", "cleiton sair"):
            print("Encerrando. Até logo!")
            break

        question = extract_question(raw)
        if not question:
            if USE_ACTIVATION_PHRASE:
                print("(Dica: comece com 'cleiton' para ativar.)")
            continue

        register_and_print_question(question)
        print("Pensando...")
        answer = generate_prompt(question)
        print(f"Cleiton: {answer}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Interface CLI para Cleiton (sem voz).")
    parser.add_argument(
        "--no-activation",
        action="store_true",
        help="Desabilita necessidade da frase de ativação."
    )
    return parser.parse_args()


def main():
    global USE_ACTIVATION_PHRASE
    args = parse_args()
    if args.no_activation:
        USE_ACTIVATION_PHRASE = False
    init_chat()
    repl()


if __name__ == "__main__":
    main()