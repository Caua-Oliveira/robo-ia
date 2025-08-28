import json
from pathlib import Path

def _get_json_data():
    """Função interna para ler e carregar o arquivo JSON."""
    data_path = Path(__file__).parent / "data" / "context.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar dados do JSON: {e}")
        return {}

def get_locais():
    """
    Obtém todas as informações de localização disponíveis, como laboratórios, NITE e outros pontos de interesse.
    Use esta função quando o usuário perguntar onde fica algum lugar.
    """
    data = _get_json_data()
    return data.get("locais", {})

def get_coordenacao():
    """
    Obtém todas as informações sobre a coordenação de cursos, incluindo nomes de coordenadores e horários de atendimento.
    Use esta função para perguntas sobre coordenadores ou seus horários.
    """
    data = _get_json_data()
    return data.get("coordenacao", {})

# Mapeamento de nomes de string para funções reais
AVAILABLE_TOOLS = {
    "get_locais": get_locais,
    "get_coordenacao": get_coordenacao,
}