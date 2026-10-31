"""CLI → Gemini → cliente MCP → servidor local → Gemini → resposta."""
import asyncio
import sys

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import LIMITE_RODADAS, MODELO, PASTA_PROJETO, SERVIDOR_MCP, obter_chave


from instrucoes import INSTRUCOES
from agente import declarar_ferramentas, processar_mensagem


async def executar():
    chave = obter_chave()
    # Usa o mesmo Python da CLI, incluindo as bibliotecas da .venv.
    parametros = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVIDOR_MCP)],
        cwd=str(PASTA_PROJETO),
    )

    async with stdio_client(parametros) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            catalogo = await sessao.list_tools()
            nomes = {ferramenta.name for ferramenta in catalogo.tools}
            print(f"[MCP] Conectado. Ferramentas: {', '.join(sorted(nomes))}")

            with genai.Client(api_key=chave) as cliente:
                async with cliente.aio as cliente_async:
                    conversa = cliente_async.chats.create(
                        model=MODELO,
                        config=types.GenerateContentConfig(
                            tools=[declarar_ferramentas(catalogo.tools)],
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                            system_instruction=INSTRUCOES,
                        ),
                    )
                    print(f"Assistente de Projetos | modelo: {MODELO}")
                    print("Digite 'sair' para encerrar.")
                    while True:
                        try:
                            mensagem = input("\nVocê: ").strip()
                        except EOFError:
                            break
                        if mensagem.lower() == "sair":
                            break
                        if not mensagem:
                            continue
                        await processar_mensagem(conversa, sessao, nomes, mensagem)
    print("Assistente: Até mais!")


if __name__ == "__main__":
    try:
        asyncio.run(executar())
    except KeyboardInterrupt:
        print("\nAssistente encerrado.")
    except Exception as erro:
        print(f"Falha ao executar o assistente: {erro}", file=sys.stderr)
        sys.exit(1)
