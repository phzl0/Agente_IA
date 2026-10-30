import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


pasta_projeto = Path(__file__).resolve().parent
load_dotenv(pasta_projeto / ".env")

chave = os.getenv("GEMINI_API_KEY")

if not chave or not chave.strip():
    raise SystemExit("Configure GEMINI_API_KEY no arquivo .env.")

with genai.Client(api_key=chave) as cliente:
    print("Consultando modelos...\n")

    for modelo in cliente.models.list():
        print(modelo.name)
