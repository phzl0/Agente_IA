import os
from pathlib import Path

from dotenv import load_dotenv


pasta_projeto = Path(__file__).resolve().parent
load_dotenv(pasta_projeto / ".env")

chave = os.getenv("GEMINI_API_KEY")

if chave and chave.strip():
    print("Chave encontrada. Configuração carregada.")
else:
    print("Chave não encontrada. Verifique o arquivo .env.")
