import re
import google.generativeai as genai

from config import MODEL_NAME
from queries import build_system_instruction
from tools import get_locais, get_coordenacao, AVAILABLE_TOOLS


USE_ACTIVATION_PHRASE = True
ACTIVATION_REGEX = re.compile(r'^\s*(e\s*a[ií]\s+cleiton|cleiton)\b[\s,]*', re.IGNORECASE)

CHAT_HISTORY = []
USER_QUESTIONS = []
chat_session = None


def init_chat():
    global chat_session
    system_instruction = build_system_instruction()

    # Informa ao modelo quais ferramentas ele pode usar
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
        tools=[get_locais, get_coordenacao]
    )
    chat_session = model.start_chat(history=[])

    print("Cleiton online (modo texto). Digite sua pergunta.")
    if USE_ACTIVATION_PHRASE:
        print("Use 'cleiton' ou 'e ai cleiton' no início para ativar. (Ex: 'cleiton onde fica o NITE?')")
    else:
        print("Ativação desabilitada; basta digitar a pergunta diretamente.")
    print("Digite 'sair' ou 'exit' para encerrar.")


def extract_question(text: str) -> str:
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

    try:
        # 1. Envia a mensagem do usuário para a IA
        response = chat_session.send_message(user_question)

        # 2. Verifica se a IA solicitou o uso de uma ferramenta
        function_call = response.candidates[0].content.parts[0].function_call
        if not function_call:
            # Se não houver chamada de função, é uma resposta de texto normal
            return (response.text or "").strip()

        # 3. Se a IA pediu uma ferramenta, executa-a
        tool_name = function_call.name
        if tool_name in AVAILABLE_TOOLS:
            print(f"IA solicitou a ferramenta: {tool_name}")
            tool_function = AVAILABLE_TOOLS[tool_name]

            # Executa a função
            tool_result = tool_function()

            # 4. Envia o resultado da ferramenta de volta para a IA (CHAMADA CORRIGIDA)
            function_response_part = {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": tool_result},
                }
            }
            response = chat_session.send_message(function_response_part)

            # A IA agora usará este resultado para formular a resposta final
            return (response.text or "").strip()
        else:
            return f"Erro: Ferramenta '{tool_name}' solicitada pela IA, mas não encontrada."

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"


def repl():
    """Simple synchronous input() loop replacing voice input."""
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando. Até logo!")
            break
        if not raw: continue

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


if __name__ == "__main__":
    init_chat()