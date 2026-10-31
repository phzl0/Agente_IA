"""RAG lexical: trechos com fontes e ranking BM25, sem API de embeddings."""
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

PASTA_DOCUMENTOS = Path(__file__).resolve().parent / "documentos"
IGNORAR = set("a o as os de da do das dos e em um uma para por com que qual quais como no na nos nas ao quanto quantos quantas sobre meu minha este esta esse essa".split())


def termos(texto: str) -> list[str]:
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", normalizado) if t not in IGNORAR]


def indexar_documentos() -> list[dict]:
    """Recria um índice em memória a cada consulta, refletindo edições locais."""
    trechos = []
    raiz = PASTA_DOCUMENTOS.resolve()
    if not raiz.exists():
        return trechos
    for arquivo in sorted(raiz.rglob("*")):
        if (not arquivo.is_file() or arquivo.is_symlink()
                or arquivo.suffix.lower() not in {".md", ".txt"}
                or any(p.startswith(".") for p in arquivo.relative_to(raiz).parts)
                or not arquivo.resolve().is_relative_to(raiz)):
            continue
        try:
            if arquivo.stat().st_size > 1_000_000:
                continue
            linhas = arquivo.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        # Janelas de até 12 linhas e 1.800 caracteres; linha longa também é dividida.
        partes = [(n, linha[i:i + 1800]) for n, linha in enumerate(linhas, 1)
                  for i in range(0, max(1, len(linha)), 1800)]
        bloco = []
        tamanho = 0
        for numero, texto in partes:
            if bloco and (len(bloco) >= 12 or tamanho + len(texto) > 1800):
                trechos.append(criar_trecho(arquivo, raiz, bloco))
                bloco, tamanho = [], 0
            bloco.append((numero, texto))
            tamanho += len(texto) + 1
        if bloco:
            trechos.append(criar_trecho(arquivo, raiz, bloco))
    return [t for t in trechos if t["termos"]]


def criar_trecho(arquivo, raiz, bloco):
    texto = "\n".join(linha for _, linha in bloco)
    return {"fonte": str(arquivo.relative_to(raiz)), "linha_inicio": bloco[0][0],
            "linha_fim": bloco[-1][0], "texto": texto, "termos": termos(texto)}


def buscar_documentos(pergunta: str, limite: int = 3) -> dict:
    """Busca trechos em documentos .md/.txt por palavras; devolve texto e fontes."""
    if not pergunta.strip() or len(pergunta) > 2000:
        return {"resultados": [], "aviso": "Informe uma pergunta entre 1 e 2.000 caracteres."}
    if not 1 <= limite <= 5:
        return {"resultados": [], "aviso": "O limite deve estar entre 1 e 5."}
    indice = indexar_documentos()
    consulta = set(termos(pergunta))
    if not indice or not consulta:
        return {"resultados": [], "aviso": "Sem documentos ou termos úteis para buscar."}
    media = sum(len(t["termos"]) for t in indice) / len(indice)
    frequencia = Counter(p for t in indice for p in set(t["termos"]))
    ranking = []
    for trecho in indice:
        contagem = Counter(trecho["termos"])
        pontos = 0.0
        for termo in consulta:
            tf = contagem[termo]
            if tf:
                idf = math.log(1 + (len(indice) - frequencia[termo] + .5) / (frequencia[termo] + .5))
                pontos += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * len(trecho["termos"]) / media))
        if pontos > 0:
            ranking.append({k: v for k, v in trecho.items() if k != "termos"} | {"pontuacao": round(pontos, 4)})
    ranking.sort(key=lambda r: r["pontuacao"], reverse=True)
    return {"resultados": ranking[:limite], "metodo": "BM25 lexical",
            "aviso": "Use apenas evidências pertinentes; coincidência de palavras não garante resposta."
            if ranking else "Nenhum trecho relacionado foi encontrado. Não invente a resposta."}
