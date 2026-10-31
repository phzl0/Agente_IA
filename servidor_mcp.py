"""Ferramentas locais expostas pelo protocolo MCP via stdio."""
from mcp.server.fastmcp import FastMCP

from rag import buscar_documentos as buscar_documentos_local

from ferramentas import listar_arquivos as listar_arquivos_local

servidor = FastMCP("Assistente de Projetos")


@servidor.tool()
def listar_arquivos() -> list[str]:
    """Lista nomes dos arquivos visíveis na raiz do projeto, sem ler conteúdo."""
    return listar_arquivos_local()


@servidor.tool()
def buscar_documentos(pergunta: str, limite: int = 3) -> dict:
    """Busca informações nos documentos locais e retorna trechos com arquivo e linhas.

    Args:
        pergunta: Pergunta ou palavras que descrevem a informação desejada.
        limite: Quantidade máxima de trechos, entre 1 e 5.
    """
    return buscar_documentos_local(pergunta, limite)


if __name__ == "__main__":
    servidor.run(transport="stdio")
