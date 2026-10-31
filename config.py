"""Configurações compartilhadas pela CLI e pelo servidor MCP."""
import os
from pathlib import Path

from dotenv import load_dotenv

PASTA_PROJETO = Path(__file__).resolve().parent
load_dotenv(PASTA_PROJETO / ".env")
MODELO = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
SERVIDOR_MCP = PASTA_PROJETO / "servidor_mcp.py"
LIMITE_RODADAS = 3


def obter_chave() -> str:
    chave = os.getenv("GEMINI_API_KEY", "").strip()
    if not chave:
        raise ValueError("Configure GEMINI_API_KEY no arquivo .env.")
    return chave
