"""Backend local da interface. A chave Gemini nunca vai para o navegador."""
import asyncio
import json
import logging
import sys
from typing import Literal
import secrets
import sqlite3
import time
import armazenamento as db
from instrucoes import INSTRUCOES

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agente import declarar_ferramentas, processar_mensagem
from config import MODELO, PASTA_PROJETO, SERVIDOR_MCP, obter_chave

def exigir_sessao(request: Request):
    conta_id = db.conta_da_sessao(request.cookies.get("agente_sessao"))
    if conta_id is None:
        raise HTTPException(401, "Entre na sua conta local.")
    return conta_id


def cookie(response, token):
    response.set_cookie("agente_sessao", token, httponly=True, samesite="strict", max_age=604800)


app = FastAPI(title="Agente IA", docs_url="/api/docs")


class Mensagem(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(min_length=1, max_length=12000)


class Pedido(BaseModel):
    mensagem: str = Field(min_length=1, max_length=2000)
    conversa_id: str | None = Field(default=None, max_length=100)
    historico: list[Mensagem] = Field(default_factory=list, max_length=40)


@app.get("/api/status")
async def status():
    try:
        obter_chave()
        configurado = True
    except ValueError:
        configurado = False
    return {"configurado": configurado, "modelo": MODELO}


def extrair_fontes(eventos):
    fontes = []
    for evento in eventos:
        if evento["ferramenta"] != "buscar_documentos":
            continue
        resultado = evento["resultado"]
        dados = resultado.get("dados")
        if not dados:
            for parte in resultado.get("conteudo", []):
                if parte.get("type") == "text":
                    try:
                        dados = json.loads(parte["text"])
                        break
                    except (ValueError, KeyError):
                        continue
        if isinstance(dados, dict):
            for fonte in dados.get("resultados", []):
                if fonte not in fontes:
                    fontes.append(fonte)
    return fontes


async def responder(pedido):
    chave = obter_chave()
    parametros = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR_MCP)], cwd=str(PASTA_PROJETO))
    eventos = []
    async with stdio_client(parametros) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            catalogo = await sessao.list_tools()
            async with genai.Client(api_key=chave).aio as cliente:
                conversa = cliente.chats.create(
                    model=MODELO,
                    history=[types.Content(role=m.role, parts=[types.Part.from_text(text=m.text)]) for m in pedido.historico],
                    config=types.GenerateContentConfig(
                        tools=[declarar_ferramentas(catalogo.tools)],
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        system_instruction=INSTRUCOES,
                    ),
                )
                texto = await processar_mensagem(conversa, sessao, {f.name for f in catalogo.tools}, pedido.mensagem, eventos)
    return {"resposta": texto, "eventos": eventos, "fontes": extrair_fontes(eventos)}


@app.post("/api/chat")
async def chat(pedido: Pedido, conta_id: int = Depends(exigir_sessao)):
    if not pedido.mensagem.strip():
        raise HTTPException(422, "Digite uma mensagem.")
    try:
        obter_chave()
    except ValueError:
        raise HTTPException(503, "Configure GEMINI_API_KEY no .env e reinicie o backend.") from None
    identificador = pedido.conversa_id or secrets.token_urlsafe(16)
    anterior = db.ler_conversa(identificador, conta_id) if pedido.conversa_id else None
    if pedido.conversa_id and anterior is None:
        raise HTTPException(404, "Conversa não encontrada.")
    mensagens = anterior['mensagens'] if anterior else []
    pedido.historico = [Mensagem(role=m["role"], text=m["text"][:12000]) for m in mensagens[-40:]]
    try:
        resultado = await asyncio.wait_for(responder(pedido), timeout=90)
        mensagens += [{"role":"user","text":pedido.mensagem},{"role":"model","text":resultado['resposta']}]
        db.salvar(identificador,mensagens,resultado['eventos'],resultado['fontes'], conta_id)
        return resultado | {"conversa_id":identificador}
    except TimeoutError:
        raise HTTPException(504, "A consulta demorou demais. Tente novamente.") from None
    except Exception:
        logging.exception("Falha na consulta do agente")
        raise HTTPException(502, "Não foi possível consultar o agente. Verifique o terminal do backend e a cota da API.") from None


class Credenciais(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    senha: str = Field(min_length=8, max_length=128)


class PerfilNovo(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    senha_atual: str = Field(default="", max_length=128)
    nova_senha: str = Field(default="", max_length=128)


@app.get("/api/conta")
async def conta(request: Request):
    conta_id = db.conta_da_sessao(request.cookies.get("agente_sessao"))
    usuario = db.perfil(conta_id) if conta_id is not None else None
    return {
        "configurada": bool(usuario or db.perfil()),
        "autenticado": usuario is not None,
        "nome": usuario["nome"] if usuario else "",
        "usuario": usuario["usuario"] if usuario else "",
    }


@app.post("/api/conta/configurar")
async def configurar(dados: Credenciais, response: Response):
    nome = dados.nome.strip()
    if not nome:
        raise HTTPException(422, "Informe seu nome de usuário.")
    try:
        conta_id = db.configurar(nome, dados.senha)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Esse nome de usuário já está em uso.") from None
    cookie(response, db.sessao_nova(conta_id))
    return db.perfil(conta_id)


# Limite simples para tentativas no ambiente local.
_tentativas=[]


@app.post("/api/conta/entrar")
async def entrar(dados: Credenciais, response: Response):
    agora=time.time()
    _tentativas[:]=[t for t in _tentativas if t>agora-60]
    if len(_tentativas)>=10:
        raise HTTPException(429,"Aguarde um minuto antes de tentar novamente.")
    conta_id = db.autenticar(dados.nome.strip(), dados.senha)
    if conta_id is None:
        _tentativas.append(agora)
        raise HTTPException(401,"Usuário ou senha incorretos.")
    _tentativas.clear()
    cookie(response,db.sessao_nova(conta_id))
    return db.perfil(conta_id)


@app.post("/api/conta/sair")
async def logout(request: Request,response: Response):
    db.sair(request.cookies.get("agente_sessao"))
    response.delete_cookie("agente_sessao")
    return {"ok":True}


@app.put("/api/perfil")
async def atualizar_perfil(dados: PerfilNovo, response: Response, conta_id: int = Depends(exigir_sessao)):
    if not dados.nome.strip():
        raise HTTPException(422,"Informe seu nome.")
    if dados.nova_senha:
        if len(dados.nova_senha)<8:
            raise HTTPException(422,"A nova senha precisa ter pelo menos 8 caracteres.")
        if not db.conferir(dados.senha_atual, conta_id):
            raise HTTPException(403,"A senha atual está incorreta.")
    db.alterar(dados.nome.strip(),dados.nova_senha or None, conta_id)
    if dados.nova_senha:
        cookie(response,db.sessao_nova(conta_id))
    return db.perfil(conta_id)


@app.get("/api/conversas")
async def conversas(conta_id: int = Depends(exigir_sessao)):
    return db.listar_conversas(conta_id)


@app.get("/api/conversas/{identificador}")
async def conversa_salva(identificador: str, conta_id: int = Depends(exigir_sessao)):
    conversa=db.ler_conversa(identificador, conta_id)
    if conversa is None:
        raise HTTPException(404,"Conversa não encontrada.")
    return conversa
