# Agente IA — beta

Assistente de projetos pelo terminal, com Gemini e um servidor MCP local. As ferramentas listam arquivos na raiz e buscam trechos em documentos locais com RAG. Não executam comandos nem modificam arquivos.

## Interface gráfica — React + FastAPI

Interface escura com chat, sugestões, nova conversa, painel de atividades MCP, trechos e fontes do RAG. As atividades aparecem após a resposta completa; não há streaming nesta versão. O histórico fica só na memória da aba e é apagado ao recarregar ou iniciar nova conversa.

Requisitos: Python 3.11+ e Node.js 20.19+ ou 22.12+ (recomendado Node 22 LTS). Mantenha sua chave no `.env` da raiz, nunca no frontend. Esta versão é local, sem autenticação nem publicação externa.

Atualize a cópia existente e inicie o backend no primeiro terminal:

```bash
cd ~/Projetos/Agente_IA
git pull --ff-only origin main
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8005
```

Em um segundo terminal, inicie a interface:

```bash
cd ~/Projetos/Agente_IA/frontend
npm ci
npm run dev
```

Abra **http://localhost:5175** no navegador. Pare cada processo com Ctrl+C no respectivo terminal. Na primeira instalação, siga também a seção de configuração do `.env` abaixo.

| Arquivo | Papel na versão gráfica |
| --- | --- |
| `frontend/src/App.tsx` | Chat, histórico da aba, atividade e fontes |
| `frontend/src/style.css` | Tema escuro e layout responsivo |
| `frontend/vite.config.ts` | Encaminha `/api` ao backend local na porta 8005 |
| `api.py` | Recebe mensagens em `POST /api/chat` e devolve resposta, eventos e fontes |
| `agente.py` | Ciclo compartilhado de chamadas de ferramentas da CLI e da interface |

Fluxo: navegador → FastAPI → Gemini → cliente MCP → ferramenta RAG → Gemini → resposta com eventos e fontes no navegador. Cada consulta web abre e fecha sua própria sessão MCP. O histórico textual enviado pela aba mantém o contexto, sem misturar conversas de usuários. Não há histórico persistente ou upload de documentos: adicione textos na pasta `documentos/`.

O indicador “API configurada” confirma a presença da chave, não valida credenciais nem cotas. Se aparecer “Backend indisponível”, confira se o primeiro terminal continua executando. Erros de consulta aparecem no chat; detalhes ficam no terminal Python. A API permite até 40 mensagens anteriores e 2.000 caracteres na pergunta. Use “Nova conversa” ao atingir o limite.

Verificação do frontend: `cd frontend` e `npm run build`. Verificações do backend: na raiz, `python -m unittest discover -s tests -v`. O teste web cobre API e fluxo MCP real com Gemini simulado; a geração real depende da chave local. A CLI original continua disponível com `python main.py`.

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

## RAG na prática

Esta versão usa busca lexical BM25 (por palavras), sem embeddings, banco externo ou nova API. A geração continua usando a API Gemini e suas cotas. Sinônimos sem palavras em comum podem não ser encontrados.

Execute a CLI e pergunte:

> Consulte os documentos: quanto XP uma missão diária concede?

O exemplo em `documentos/exemplo_progress_hub.md` é fictício e informa 300 XP. O terminal mostra a chamada `buscar_documentos`, os trechos retornados e, depois, a resposta do modelo. A instrução do agente pede citações no formato `[arquivo:linhas]`. A geração das citações depende do modelo; não é uma validação automática de veracidade.

Para observar a diferença, edite o valor no documento e repita: “Consulte novamente os documentos: quanto XP uma missão diária concede?”. A próxima consulta reconstrói o índice com o novo conteúdo.

| Ponto | O que acontece |
| --- | --- |
| `documentos/` | Fonte dos arquivos `.md` e `.txt` em UTF-8 |
| `rag.py` / `indexar_documentos` | Divide textos em trechos com arquivo e linhas e cria índice em memória |
| `rag.py` / `buscar_documentos` | Classifica por BM25 e retorna até 3 trechos por padrão |
| `servidor_mcp.py` / `buscar_documentos` | Disponibiliza a busca como ferramenta MCP |
| `main.py` / `processar_mensagem` | Envia ao Gemini o resultado recuperado para gerar a resposta |

Fluxo: pergunta → Gemini solicita busca → MCP chama RAG → trechos e fontes → Gemini responde.

Adicione seus próprios `.md` ou `.txt` dentro de `documentos/`, inclusive em subpastas. Cada consulta refaz o índice: não precisa executar comando de indexação. Arquivos ocultos, links simbólicos, arquivos inválidos em UTF-8 e arquivos maiores que 1 MB são ignorados. PDFs ainda não são suportados. Os trechos têm até 1.800 caracteres, com até 12 linhas por trecho; a ferramenta devolve no máximo 5 trechos. É uma implementação didática para pequenas coleções, sem persistência nem busca semântica.

Os trechos recuperados são enviados ao Google para responder à pergunta. Documentos são tratados como dados de consulta, e a instrução do agente pede que ele ignore comandos contidos neles. Se não houver evidência suficiente, a orientação é dizer que não encontrou a resposta; um resultado lexical não garante que o trecho seja relevante.

## Verificação do projeto

```bash
python -m unittest discover -s tests -v
```

O teste inicia o servidor MCP real, descobre e chama a ferramenta, confere o retorno ao ciclo de conversa e a rejeição de ferramenta inexistente. Também verifica a busca RAG via MCP, fontes, atualização dos documentos, ausência de resultados e limites dos trechos. A resposta do Gemini é simulada: não exige chave e não consome cota. A chamada real ao Google depende da chave local do usuário.

Dependências diretas fixadas nas versões verificadas: Gemini SDK 2.34.0, MCP Python SDK 1.30.0 (API v1) e python-dotenv 1.2.4. Os scripts `testar_ia.py`, `listar_modelos.py` e `verificar_config.py` permanecem como exemplos das etapas anteriores; a entrada principal é `main.py`.
