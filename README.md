# Agente IA — beta

Assistente de projetos pelo terminal, com Gemini e um servidor MCP local. A ferramenta atual lista nomes de arquivos na raiz do projeto. Não lê conteúdo, não executa comandos e não implementa RAG ainda.

## Executar no Ubuntu

Na sua cópia já existente:

```bash
cd ~/Projetos/Agente_IA
git pull --ff-only origin main
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Na primeira instalação:

```bash
git clone git@github.com:phzl0/Agente_IA.git
cd Agente_IA
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Preencha `GEMINI_API_KEY` com sua chave. O `GEMINI_MODEL` é opcional e usa `gemini-3.5-flash-lite` por padrão. Não substitua seu `.env` existente: ele continua válido. O arquivo não deve ser enviado ao GitHub. A disponibilidade, as cotas e a cobrança dependem do modelo e da conta no provedor.

Depois execute `python main.py`. Pergunte: “Consulte os arquivos da pasta principal”. Digite `sair` ou use Ctrl+C para encerrar. A CLI inicia e encerra o servidor automaticamente; não há porta HTTP nem segundo terminal.

## Onde cada conexão acontece

| Arquivo / ponto | Responsabilidade |
| --- | --- |
| `config.py` / `load_dotenv` | Lê o `.env` na pasta do projeto |
| `config.py` / `obter_chave`, `MODELO` | Define chave da API e modelo |
| `main.py` / `genai.Client` | Configura o cliente da API do Gemini |
| `main.py` / `conversa.send_message` | Envia mensagens e resultados ao Google pela internet |
| `main.py` / `StdioServerParameters` | Define o Python e o script do servidor local |
| `main.py` / `stdio_client`, `ClientSession` | Abre o processo MCP e inicializa a conexão |
| `main.py` / `list_tools`, `declarar_ferramentas` | Descobre ferramentas e traduz o catálogo para o Gemini |
| `main.py` / `processar_mensagem`, `call_tool` | Recebe o pedido do modelo e o encaminha ao MCP |
| `servidor_mcp.py` / `@servidor.tool()` | Registra a ferramenta no servidor |
| `ferramentas.py` / `listar_arquivos` | Consulta os nomes no sistema de arquivos |

## Fluxo

1. A CLI inicia um processo Python para o servidor MCP, usando o mesmo ambiente virtual.
2. Cliente e servidor fazem a inicialização MCP; a CLI consulta o catálogo de ferramentas.
3. O Gemini recebe a mensagem e as descrições das ferramentas.
4. Se o modelo pedir uma ferramenta, a CLI encaminha nome e argumentos pelo MCP.
5. O servidor executa a função local e retorna os dados.
6. A CLI envia o resultado ao Gemini, que produz a resposta exibida no terminal.

MCP usa `stdio`: entrada e saída padrão carregam o protocolo entre processos. Logs da ferramenta usam `stderr` para não corromper essa comunicação. O servidor mantém sua pasta de consulta fixa na raiz do projeto. O Gemini recebe os nomes retornados, não acesso direto ao computador.

O histórico vive na memória do processo e é reenviado pelo SDK nas próximas mensagens. Ao fechar a CLI, ele é perdido. Cada turno permite até três rodadas de ferramentas; falhas encerram a sessão com diagnóstico em vez de continuar com pedidos incompletos. A resposta final é impressa uma única vez.

## Próxima etapa: RAG

RAG será uma ferramenta adicional: documentos serão divididos em trechos e indexados; uma busca recuperará os trechos relevantes para a pergunta; esses trechos e suas fontes serão devolvidos por MCP ao modelo. MCP cuida da conexão com a ferramenta. RAG cuida da recuperação do conteúdo. Essa etapa ainda não está implementada.

## Verificação do projeto

```bash
python -m unittest discover -s tests -v
```

O teste inicia o servidor MCP real, descobre e chama a ferramenta, confere o retorno ao ciclo de conversa e a rejeição de ferramenta inexistente. A resposta do Gemini é simulada: não exige chave e não consome cota. A chamada real ao Google depende da chave local do usuário.

Dependências diretas fixadas nas versões verificadas: Gemini SDK 2.34.0, MCP Python SDK 1.30.0 (API v1) e python-dotenv 1.2.4. Os scripts `testar_ia.py`, `listar_modelos.py` e `verificar_config.py` permanecem como exemplos das etapas anteriores; a entrada principal é `main.py`.
