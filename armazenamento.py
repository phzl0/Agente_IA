"""Conta local, sessões e conversas persistidas em SQLite."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

BANCO = Path(__file__).resolve().parent / '.data' / 'agente.db'


@contextmanager
def conexao():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(BANCO) as banco:
        banco.row_factory = sqlite3.Row
        banco.executescript('''
            CREATE TABLE IF NOT EXISTS perfil(id INTEGER PRIMARY KEY, nome TEXT, sal TEXT, senha TEXT);
            CREATE TABLE IF NOT EXISTS sessoes(token TEXT PRIMARY KEY, expira REAL);
            CREATE TABLE IF NOT EXISTS conversas(id TEXT PRIMARY KEY, titulo TEXT, mensagens TEXT, eventos TEXT, fontes TEXT, atualizado REAL);
        ''')
        yield banco


def hash_senha(senha, sal):
    return hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=16384, r=8, p=1).hex()


def perfil():
    with conexao() as banco:
        linha = banco.execute('SELECT nome FROM perfil WHERE id=1').fetchone()
        return dict(linha) if linha else None


def configurar(nome, senha):
    sal = secrets.token_hex(16)
    with conexao() as banco:
        banco.execute('INSERT INTO perfil VALUES(1,?,?,?)', (nome, sal, hash_senha(senha, sal)))


def conferir(senha):
    with conexao() as banco:
        linha = banco.execute('SELECT sal,senha FROM perfil WHERE id=1').fetchone()
        return bool(linha and hmac.compare_digest(linha['senha'], hash_senha(senha, linha['sal'])))


def sessao_nova():
    token = secrets.token_urlsafe(32)
    with conexao() as banco:
        banco.execute('DELETE FROM sessoes WHERE expira < ?', (time.time(),))
        banco.execute('INSERT INTO sessoes VALUES(?,?)', (hashlib.sha256(token.encode()).hexdigest(),time.time()+604800))
    return token


def sessao_valida(token):
    if not token:
        return False
    with conexao() as banco:
        return banco.execute('SELECT 1 FROM sessoes WHERE token=? AND expira>?', (hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone() is not None


def sair(token):
    with conexao() as banco:
        banco.execute('DELETE FROM sessoes WHERE token=?',(hashlib.sha256((token or '').encode()).hexdigest(),))


def alterar(nome, senha=None):
    with conexao() as banco:
        banco.execute('UPDATE perfil SET nome=? WHERE id=1',(nome,))
        if senha:
            sal=secrets.token_hex(16)
            banco.execute('UPDATE perfil SET sal=?,senha=? WHERE id=1',(sal,hash_senha(senha,sal)))
            banco.execute('DELETE FROM sessoes')


def listar_conversas():
    with conexao() as banco:
        return [dict(r) for r in banco.execute('SELECT id,titulo,atualizado FROM conversas ORDER BY atualizado DESC')]


def ler_conversa(identificador):
    with conexao() as banco:
        r=banco.execute('SELECT * FROM conversas WHERE id=?',(identificador,)).fetchone()
        if not r:
            return None
        resultado=dict(r)
        for campo in ('mensagens','eventos','fontes'):
            resultado[campo]=json.loads(resultado[campo])
        return resultado


def salvar(identificador, mensagens, eventos, fontes):
    with conexao() as banco:
        banco.execute('INSERT OR REPLACE INTO conversas VALUES(?,?,?,?,?,?)',(
            identificador,mensagens[0]['text'][:65],json.dumps(mensagens),json.dumps(eventos),json.dumps(fontes),time.time()))
