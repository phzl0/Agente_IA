# Agente IA — Beta

> **Projeto em fase beta.** Interface, recursos e integrações estão em evolução. Desenvolvido para aprender na prática como um agente conecta uma interface, um modelo de linguagem, ferramentas MCP e busca em documentos com RAG.

Assistente de IA com **chat web em React**, **backend Python/FastAPI**, **API Gemini**, **servidor MCP local** e **RAG lexical**. Também pode ser utilizado pelo terminal (CLI).

## Comece aqui: executar no seu computador

O projeto funciona localmente, sem Docker ou hospedagem contratada. **É necessário ter internet e uma chave própria da API Gemini para receber respostas da IA.** A instalação das dependências também precisa de internet.

Cada pessoa usa sua própria chave. Disponibilidade dos modelos, cotas gratuitas e cobrança dependem da conta no Google; o projeto não inclui créditos nem garante uso gratuito. A chave fica no backend, no arquivo `.env`.

| Requisito | Versão / finalidade |
| --- | --- |
| Git | Baixar e atualizar o projeto |
| Python | 3.11 ou superior, com suporte a ambientes virtuais |
| Node.js + npm | Node 22.12+ ou uma versão LTS mais recente compatível com Vite 6 |
| Chave Gemini | Obter no [Google AI Studio](https://aistudio.google.com/app/apikey) |

**Portas utilizadas:** interface `5175` e backend `8005`. Os servidores ficam vinculados ao computador local. Esta beta não foi preparada para exposição pública nem para múltiplos usuários.

### Linux / Ubuntu

**1. Confira os requisitos.** Instale Git, Python e [Node.js](https://nodejs.org/) se ainda não estiverem disponíveis.

```bash
git --version
python3 --version
node --version
npm --version
```

No Ubuntu, caso falte suporte ao ambiente virtual:

```bash
sudo apt update
sudo apt install python3-venv
```

Se o Python pedir um pacote específico, como `python3.14-venv`, instale o pacote correspondente à versão utilizada.

**2. Baixe o projeto.** A URL HTTPS abaixo não exige configurar uma chave SSH para clonar este repositório público.

```bash
mkdir -p ~/Projetos
cd ~/Projetos
git clone https://github.com/phzl0/Agente_IA.git
cd Agente_IA
```

Se a pasta já existir, siga a seção [Atualizar uma instalação existente](#atualizar-uma-instalação-existente), sem clonar novamente dentro dela.

**3. Crie o ambiente Python e instale as bibliotecas.** Execute sem `sudo`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**4. Configure sua chave Gemini.** Estes comandos são apenas para a primeira instalação:

```bash
cp .env.example .env
nano .env
```

Preencha a chave no arquivo:

```dotenv
GEMINI_API_KEY=cole_sua_chave_aqui
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua `cole_sua_chave_aqui` pela chave real, sem espaços extras. No Nano: salve com `Ctrl+O`, pressione `Enter` e saia com `Ctrl+X`. O modelo é configurável; se ele não estiver disponível na sua conta, escolha um modelo de texto compatível com chamadas de ferramentas e ajuste `GEMINI_MODEL`.

**Não envie o `.env` ou a chave ao GitHub.** O `.gitignore` já ignora esse arquivo. Não copie o `.env.example` sobre um `.env` que já contém sua configuração.

**5. Inicie o backend no primeiro terminal.** Continue na pasta `Agente_IA`, com o ambiente virtual ativo:

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8005
```

Aguarde a mensagem de inicialização em `http://127.0.0.1:8005`. **Deixe esse terminal aberto.**

**6. Abra um segundo terminal e inicie a interface:**

```bash
cd ~/Projetos/Agente_IA/frontend
npm ci
npm run dev
```

**7. Abra [http://localhost:5175](http://localhost:5175).** Crie sua conta local com nome e senha de pelo menos 8 caracteres. Não existe usuário ou senha padrão. Essa senha é para entrar no projeto; não é a senha da conta Google nem a chave da API.

### Windows — PowerShell

**1. Instale os requisitos:** [Git](https://git-scm.com/downloads), [Python 3.11+](https://www.python.org/downloads/windows/) e [Node.js LTS](https://nodejs.org/). Abra um novo PowerShell após a instalação e confira:

```powershell
git --version
py -3 --version
node --version
npm --version
```

Se `py` não existir, mas `python --version` mostrar uma versão compatível, use `python` no lugar de `py -3` no comando que cria o ambiente virtual.

**2. Baixe o projeto:**

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\Projetos" | Out-Null
Set-Location "$HOME\Projetos"
git clone https://github.com/phzl0/Agente_IA.git
Set-Location Agente_IA
```

**3. Crie o ambiente e instale as bibliotecas:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Usamos o Python do ambiente diretamente, sem precisar ativá-lo nem alterar a política de execução do PowerShell.

**4. Crie o `.env` na primeira instalação e edite no Bloco de Notas:**

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `GEMINI_API_KEY` e mantenha ou ajuste `GEMINI_MODEL`, conforme o exemplo da seção Linux. Salve como `.env`, sem acrescentar `.txt`. Não sobrescreva esse arquivo em atualizações.

**5. No primeiro terminal, inicie o backend:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8005
```

Deixe esse terminal aberto.

**6. Em um segundo PowerShell, inicie a interface:**

```powershell
Set-Location "$HOME\Projetos\Agente_IA\frontend"
npm ci
npm run dev
```

**7. Abra [http://localhost:5175](http://localhost:5175)** e crie sua conta local. Se o PowerShell bloquear `npm.ps1`, use `npm.cmd ci` e `npm.cmd run dev`, sem alterar a política de execução.

As verificações automatizadas e a conferência visual foram executadas em Linux. O roteiro PowerShell utiliza os caminhos equivalentes, mas não foi executado em uma máquina Windows nesta etapa.

## Experimente a beta

No chat, teste:

- **Pergunta geral:** “O que é uma API?” ou “O que é a Binance?”. Não exige documentos locais.
- **Ferramenta MCP:** “Liste os arquivos da pasta principal deste projeto.”
- **RAG:** “Consulte os documentos: quanto XP uma missão diária concede?”

O documento `documentos/exemplo_progress_hub.md` contém **regras fictícias de demonstração**, incluindo 300 XP por missão diária. Abra **Contexto** para ver as ferramentas utilizadas e os trechos recuperados na última consulta. Esses dados aparecem quando a resposta termina, sem streaming.

Adicione arquivos `.md` e `.txt` em UTF-8 na pasta `documentos/`, inclusive em subpastas. A próxima busca já usa o conteúdo atualizado: não precisa indexar manualmente. Os trechos encontrados são enviados à API Gemini para gerar a resposta.

## Atualizar uma instalação existente

Pare backend e interface com `Ctrl+C` nos respectivos terminais antes de atualizar. Na raiz do projeto:

```bash
git pull --ff-only origin main
```

**Linux — primeiro terminal:**

```bash
cd ~/Projetos/Agente_IA
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8005
```

**Windows — primeiro PowerShell:**

```powershell
Set-Location "$HOME\Projetos\Agente_IA"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8005
```

**Segundo terminal, dentro de `Agente_IA/frontend`:**

```bash
npm ci
npm run dev
```

Se a tela parecer antiga, recarregue com `Ctrl+Shift+R`. Preserve o `.env` e a pasta `.data/`: eles contêm sua configuração e seus dados locais.

## Parar e abrir novamente

Use `Ctrl+C` em cada terminal para parar. Isso não apaga as conversas.

Para abrir novamente, inicie o backend e depois execute `npm run dev` na pasta `frontend`. Não precisa clonar, criar outra `.venv`, copiar o `.env` ou instalar bibliotecas novamente, a menos que esteja atualizando dependências.

## Problemas comuns

| Problema | O que fazer |
| --- | --- |
| `ensurepip is not available` | Instale `python3-venv` ou o pacote específico indicado pelo Python e recrie `.venv` sem `sudo`. |
| `Permission denied` após criar `.venv` com `sudo` | Na raiz do projeto, ajuste apenas essa pasta com `sudo chown -R "$USER":"$(id -gn)" .venv` e recrie com `python3 -m venv .venv`. |
| `ModuleNotFoundError` | Use o Python da `.venv` e instale `requirements.txt`. No Windows, execute pelo caminho `.venv\Scripts\python.exe`. |
| `npm` não encontrado ou Node incompatível | Instale uma versão compatível do Node.js e abra um novo terminal. |
| `Port 5175 is already in use` | Confira se outra instância do frontend está aberta. Se a porta pertencer a outro projeto, altere `server.port` em `frontend/vite.config.ts`. |
| Backend: `address already in use` na porta `8005` | Confira se já iniciou o backend. Para usar outra porta, altere o comando `--port` e o destino do proxy `/api` em `frontend/vite.config.ts` para o mesmo número. |
| “Backend indisponível” ou erro ao criar conta | Inicie o backend e confira se o proxy aponta para a porta dele. Recarregue a página após iniciar. |
| “Configure GEMINI_API_KEY” | Confira o `.env` na raiz, o nome da variável e se o arquivo não foi salvo como `.env.txt`. Reinicie o backend após editar. |
| “API configurada”, mas o chat falha | O indicador confirma apenas a presença da chave. Veja o erro no terminal Python: credenciais, cota, modelo ou acesso à internet podem impedir a consulta. |
| Modelo não encontrado / erro 404 | Ajuste `GEMINI_MODEL` para um modelo compatível disponível à sua conta e reinicie o backend. |
| Limite de requisições / erro 429 | Verifique as cotas do projeto no Google AI Studio e aguarde a liberação indicada pelo provedor. |
| Conversa nova não aparece na lista | Ela é salva depois da primeira resposta concluída com sucesso. Conversas vazias ou solicitações que falharam não criam histórico. |
| RAG não encontra uma resposta | Use `.md` ou `.txt` em UTF-8 dentro de `documentos/` e termos presentes no texto. A busca é por palavras, não por significado. |

## Conta, perfil e dados locais

Para criar outra conta, saia do perfil e clique em **Cadastrar nova conta** na tela de login. Escolha um usuário único e uma senha de 8 a 128 caracteres. Cada conta tem suas próprias conversas.

Se você já tinha conta antes da atualização, entre com o nome que constava no seu perfil e a senha existente. O banco é atualizado automaticamente e mantém as conversas na conta original.

Clique no perfil para consultar seu usuário de acesso, alterar o nome de exibição ou trocar a senha. A troca de senha exige a senha atual e encerra as outras sessões dessa conta. O nome de exibição pode mudar sem alterar o usuário usado no login.

O SQLite em `.data/agente.db` guarda o perfil, o hash scrypt da senha, sessões e conversas. `.data/` e `.env` são ignorados pelo Git e não são transferidos com `git clone` ou `git pull`.

Para fazer backup, pare o backend e copie a pasta `.data/` e o `.env` para um local privado. Preserve esses arquivos ao mudar de computador ou reinstalar. Não há recuperação de senha pela interface nesta beta.

As conversas completas ficam salvas; o modelo recebe as últimas 40 mensagens como contexto. Cada conversa também preserva as fontes e atividades da última consulta. Na CLI, o histórico fica somente na memória até encerrar o programa; o login web não bloqueia a CLI para o usuário do sistema operacional.

## Usar somente pelo terminal — CLI

Após instalar as dependências Python e configurar o `.env`, não é necessário iniciar FastAPI ou React.

**Linux, na raiz do projeto:**

```bash
source .venv/bin/activate
python main.py
```

**Windows / PowerShell, na raiz:**

```powershell
.\.venv\Scripts\python.exe main.py
```

Digite `sair` ou pressione `Ctrl+C` para encerrar. A própria CLI inicia e encerra o servidor MCP.

## Tecnologias e fluxo

| Camada | Tecnologia / responsabilidade |
| --- | --- |
| Interface | React, TypeScript e Vite |
| Backend web | Python, FastAPI e Uvicorn |
| Modelo | API Gemini pelo SDK `google-genai` |
| Ferramentas | MCP Python SDK v1, transporte local `stdio` |
| RAG | Recuperação lexical BM25, índice em memória |
| Persistência | SQLite |
| Respostas | Markdown com `react-markdown` e `remark-gfm` |

**Fluxo web:** React → FastAPI → agente → Gemini → pedido de ferramenta → MCP → função local / RAG → resultado ao Gemini → resposta no chat.

O modelo solicita uma ferramenta; o Python executa. MCP padroniza a conexão. RAG busca trechos e fontes para fundamentar a geração. Quando uma pergunta é geral, o modelo pode responder sem consultar os documentos.

| Arquivo | Onde a implementação acontece |
| --- | --- |
| `config.py` | Carrega `.env`, chave, modelo e caminhos |
| `api.py` | Endpoints de chat, conta, perfil e conversas; conexão com Gemini e MCP na web |
| `main.py` | Entrada da CLI e conexão com Gemini/MCP pelo terminal |
| `agente.py` | Ciclo compartilhado de pedidos e resultados de ferramentas |
| `instrucoes.py` | Comportamento geral e padrão de resposta do modelo |
| `servidor_mcp.py` | Registro das ferramentas `listar_arquivos` e `buscar_documentos` |
| `ferramentas.py` | Lista nomes de arquivos na raiz do projeto |
| `rag.py` | Divide documentos em trechos e recupera os relevantes |
| `armazenamento.py` | Conta, sessões e conversas no SQLite |
| `frontend/src/App.tsx` | Chat, histórico, perfil e painel Contexto |
| `frontend/src/Resposta.tsx` | Negrito, listas, tabelas, cards e código com botão de copiar |
| `frontend/vite.config.ts` | Porta da interface e proxy de `/api` para FastAPI |

## Limites da beta

- Não há busca na internet: notícias, preços ou mudanças recentes não são verificados pelo agente.
- O RAG usa palavras e BM25, sem embeddings ou banco vetorial; sinônimos sem palavras em comum podem não ser encontrados.
- PDFs e upload pela interface ainda não são suportados. Arquivos ocultos, links simbólicos, textos inválidos em UTF-8 e arquivos maiores que 1 MB são ignorados.
- Trechos de até 1.800 caracteres e 12 linhas; a ferramenta retorna até 3 trechos por padrão, com limite máximo de 5.
- Cada turno permite até três rodadas de ferramentas. A listagem informa somente nomes; as ferramentas atuais não editam arquivos nem executam comandos.
- Fontes e respostas são geradas com auxílio do modelo; uma citação não garante que a conclusão esteja correta.
- HTML bruto não é executado no chat. Markdown é suportado, mas LaTeX e diagramas interativos ainda não.

## Verificações

**Backend — Linux, com `.venv` ativa:**

```bash
python -m unittest discover -s tests -v
```

**Backend — Windows / PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Frontend — dentro de `frontend`, nos dois sistemas:**

```bash
npm ci
npm test
npm run build
```

Os testes do backend verificam API, conta/senha, persistência, MCP real e recuperação RAG com o Gemini simulado, sem chave ou consumo de cota. O frontend testa a renderização Markdown e bloqueio de HTML executável. A geração real exige a chave local do usuário.

Os scripts `testar_ia.py`, `listar_modelos.py` e `verificar_config.py` permanecem como exemplos das etapas iniciais de aprendizado. As entradas principais são a interface web e `main.py`.
