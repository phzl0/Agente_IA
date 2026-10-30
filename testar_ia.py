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
    print("Enviando pergunta ao Gemini...")

    resposta = cliente.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Explique em português, em duas frases, o que é uma API.",
    )

    print("\nResposta da IA:")
    print(resposta.text)
