import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ferramentas import listar_arquivos


def main():
    pasta_projeto = Path(__file__).resolve().parent
    load_dotenv(pasta_projeto / ".env")

    chave = os.getenv("GEMINI_API_KEY")

    if not chave or not chave.strip():
        raise SystemExit("Configure GEMINI_API_KEY no arquivo .env.")

    with genai.Client(api_key=chave) as cliente:
        conversa = cliente.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                tools=[listar_arquivos],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True,
                ),
                system_instruction=(
                    "Você é um assistente de projetos. "
                    "Use listar_arquivos para consultar os arquivos "
                    "atuais da pasta principal quando necessário. "
                    "Essa ferramenta informa apenas nomes; "
                    "não permite ler o conteúdo dos arquivos."
                ),
            ),
        )

        print("Assistente de Projetos")
        print("Digite 'sair' para encerrar.")

        while True:
            mensagem = input("\nVocê: ").strip()

            if mensagem.lower() == "sair":
                print("Assistente: Até mais!")
                break

            if not mensagem:
                print("Assistente: Digite uma mensagem.")
                continue

            print("Consultando IA...")
            resposta = conversa.send_message(mensagem)

            rodadas = 0
            if resposta.text:
                print(f"\nAssistente: {resposta.text}")

            while resposta.function_calls:
                rodadas += 1

                if rodadas > 3:
                    print("Limite de chamadas de ferramentas atingido.")
                    return

                resultados = []

                for chamada in resposta.function_calls:
                    print("\n[Pedido de ferramenta]")
                    print(f"Nome: {chamada.name}")
                    print(f"Argumentos: {chamada.args}")

                    if chamada.name != "listar_arquivos":
                        resultado = {"erro": "Ferramenta desconhecida."}
                    elif chamada.args:
                        resultado = {"erro": "Esta ferramenta não recebe argumentos."}
                    else:
                        arquivos = listar_arquivos()
                        resultado = {"arquivos": arquivos}

                    print(f"[Resultado] {resultado}")

                    resultados.append(
                        types.Part.from_function_response(
                            name=chamada.name,
                            response=resultado,
                        )
                    )

                resposta = conversa.send_message(resultados)

            if resposta.text:
                print(f"\nAssistente: {resposta.text}")


if __name__ == "__main__":
    main()
