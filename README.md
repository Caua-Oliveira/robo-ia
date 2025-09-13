# Cleiton: Assistente Universitário

Este é "Cleiton", um assistente de voz criado para responder perguntas sobre a universidade. Ele escuta suas perguntas e busca as respostas em um arquivo de dados local.

## Como Usar

Siga os passos abaixo para executar o assistente.

1.  **Instale as dependências:**
    Abra o terminal na pasta do projeto e execute o comando:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Adicione sua Chave de API:**
    Abra o arquivo `config.py` e insira sua chave do Google Gemini na variável `GEMINI_API_KEY`.
    ```python
    # Em config.py
    GEMINI_API_KEY = "SUA_CHAVE_DE_API_AQUI"
    ```

3.  **Execute o programa:**
    Com tudo configurado, inicie a aplicação:
    ```bash
    python main.py
    ```

4.  **Faça uma pergunta:**
    Quando o terminal mostrar "Ouvindo...", comece com a frase de ativação **"Ei Cleiton"** ou **"Cleiton"**, seguida pela sua pergunta.

    * *"Ei Cleiton, onde fica o NITE?"*
    * *"Cleiton, qual o horário do coordenador de computação?"*

5.  **Encerre o programa:**
    Para parar a aplicação, diga **"Cleiton sair"** ou pressione `Ctrl + C` no terminal.
    > Para interromper a fala do robô a qualquer momento, pressione a tecla `Espaço`.

## 📂 O que cada arquivo faz

* `main.py`: Arquivo principal que **inicia a aplicação**.
* `chat.py`: Contém a **lógica central** para ouvir o usuário, enviar a pergunta para a IA e processar a resposta.
* `audio.py`: Responsável por **converter a sua fala em texto** e a resposta do robô em áudio.
* `config.py`: Guarda as **configurações do projeto**, como a chave da API e os parâmetros de áudio.
* `tools.py`: Define as **"ferramentas"** que a IA usa para consultar informações específicas, como locais e horários.
* `queries.py`: Contém a **instrução principal** que diz à IA como ela deve se comportar (ser o assistente "Cleiton").
* `data/context.json`: É a **"base de dados"** do robô. Todas as informações sobre locais e coordenação estão aqui.
