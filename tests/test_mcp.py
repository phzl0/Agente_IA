"""Integração MCP real; respostas do Gemini simuladas, sem chave ou cobrança."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import PASTA_PROJETO, SERVIDOR_MCP
from main import declarar_ferramentas, processar_mensagem


class ConversaSimulada:
    def __init__(self):
        self.mensagens = []

    async def send_message(self, mensagem):
        self.mensagens.append(mensagem)
        if len(self.mensagens) == 1:
            return SimpleNamespace(function_calls=[types.FunctionCall(name="listar_arquivos", args={})])
        return SimpleNamespace(function_calls=None, text="Lista recebida.")


class IntegracaoMCP(unittest.IsolatedAsyncioTestCase):
    async def test_descoberta_execucao_e_retorno_ao_modelo(self):
        parametros = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR_MCP)])
        async with stdio_client(parametros) as (leitura, escrita):
            async with ClientSession(leitura, escrita) as sessao:
                await sessao.initialize()
                catalogo = await sessao.list_tools()
                nomes = {f.name for f in catalogo.tools}
                self.assertEqual(nomes, {"listar_arquivos", "buscar_documentos"})
                declaracao = declarar_ferramentas(catalogo.tools)
                self.assertEqual({d.name for d in declaracao.function_declarations}, nomes)
                conversa = ConversaSimulada()
                await processar_mensagem(conversa, sessao, nomes, "Liste os arquivos")
                retorno = conversa.mensagens[1][0].function_response.response
                self.assertFalse(retorno["erro"])
                self.assertIn("main.py", str(retorno))
                self.assertNotIn(".env", str(retorno))
                busca = await sessao.call_tool("buscar_documentos", {"pergunta": "quantos XP missão diária"})
                self.assertFalse(busca.isError)
                self.assertIn("300", str(busca.content))
                rejeitado = await sessao.call_tool("ferramenta_inexistente", {})
                self.assertTrue(rejeitado.isError)


if __name__ == "__main__":
    unittest.main()
