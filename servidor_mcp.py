"""Ferramentas locais expostas pelo protocolo MCP via stdio."""
from mcp.server.fastmcp import FastMCP

from ferramentas import listar_arquivos as listar_arquivos_local

servidor = FastMCP("Assistente de Projetos")


@servidor.tool()
def listar_arquivos() -> list[str]:
    """Lista nomes dos arquivos visíveis na raiz do projeto, sem ler conteúdo."""
    return listar_arquivos_local()


if __name__ == "__main__":
    servidor.run(transport="stdio")
