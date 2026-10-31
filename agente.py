"""Ciclo do agente compartilhado pela CLI e pela API web."""
from google.genai import types
from config import LIMITE_RODADAS

def declarar_ferramentas(ferramentas):
    """Converte o catálogo MCP em declarações que o Gemini entende."""
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name=ferramenta.name,
            description=ferramenta.description or "",
            parameters_json_schema=ferramenta.inputSchema,
        )
        for ferramenta in ferramentas
    ])


async def processar_mensagem(conversa, sessao, nomes_permitidos, mensagem, eventos=None):
    resposta = await conversa.send_message(mensagem)
    rodadas = 0

    while resposta.function_calls:
        if rodadas >= LIMITE_RODADAS:
            # A sessão contém pedidos sem resposta; encerre em vez de reutilizá-la.
            raise RuntimeError("Limite de rodadas de ferramentas atingido. Reinicie a CLI.")
        rodadas += 1
        resultados = []

        for chamada in resposta.function_calls:
            print(f"[MCP] Pedido: {chamada.name} | argumentos: {chamada.args or {}}")
            if chamada.name not in nomes_permitidos:
                resultado = {"erro": "Ferramenta não disponibilizada pelo servidor."}
            else:
                retorno = await sessao.call_tool(chamada.name, arguments=chamada.args or {})
                resultado = {
                    "erro": retorno.isError,
                    "dados": retorno.structuredContent,
                    "conteudo": [item.model_dump(mode="json") for item in retorno.content],
                }
            print(f"[MCP] Resultado: {resultado}")
            if eventos is not None:
                eventos.append({"ferramenta": chamada.name, "argumentos": chamada.args or {}, "resultado": resultado})
            resultados.append(types.Part.from_function_response(
                name=chamada.name, response=resultado,
            ))

        resposta = await conversa.send_message(resultados)

    texto = resposta.text or "O modelo não retornou texto."
    if eventos is None:
        print(f"\nAssistente: {texto}")
    return texto


