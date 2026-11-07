"""Conta local, sessões e conversas persistidas em SQLite."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path

BANCO = Path(__file__).resolve().parent / '.data' / 'agente.db'


@contextmanager
def conexao():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(BANCO)) as banco, banco:
        banco.row_factory = sqlite3.Row
        banco.executescript('''
            CREATE TABLE IF NOT EXISTS perfil(id INTEGER PRIMARY KEY, nome TEXT, sal TEXT, senha TEXT);
            CREATE TABLE IF NOT EXISTS sessoes(token TEXT PRIMARY KEY, expira REAL);
            CREATE TABLE IF NOT EXISTS conversas(id TEXT PRIMARY KEY, titulo TEXT, mensagens TEXT, eventos TEXT, fontes TEXT, atualizado REAL);
        ''')
        def perfil_migrado():
            return any(linha["name"] == "usuario" for linha in banco.execute("PRAGMA table_info(perfil)"))

        if not perfil_migrado():
            banco.execute("BEGIN IMMEDIATE")
            if not perfil_migrado():
                banco.execute("ALTER TABLE perfil ADD COLUMN usuario TEXT")
                for linha in banco.execute("SELECT id, nome FROM perfil").fetchall():
                    banco.execute("UPDATE perfil SET usuario=? WHERE id=?", (linha["nome"].strip().casefold(), linha["id"]))
                banco.execute("CREATE UNIQUE INDEX perfil_usuario ON perfil(usuario)")
                banco.execute("ALTER TABLE sessoes ADD COLUMN conta_id INTEGER NOT NULL DEFAULT 1")
                banco.execute("ALTER TABLE conversas ADD COLUMN conta_id INTEGER NOT NULL DEFAULT 1")
                banco.execute("CREATE INDEX conversas_conta ON conversas(conta_id, atualizado DESC)")
            banco.commit()
        yield banco


def hash_senha(senha, sal):
    return hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=16384, r=8, p=1).hex()


def perfil(conta_id=1):
    with conexao() as banco:
        linha = banco.execute('SELECT nome, usuario FROM perfil WHERE id=?', (conta_id,)).fetchone()
        return dict(linha) if linha else None


def configurar(nome, senha):
    sal = secrets.token_hex(16)
    with conexao() as banco:
        cursor = banco.execute(
            'INSERT INTO perfil(nome, sal, senha, usuario) VALUES(?,?,?,?)',
            (nome, sal, hash_senha(senha, sal), nome.casefold()),
        )
        return cursor.lastrowid


def autenticar(usuario, senha):
    with conexao() as banco:
        linha = banco.execute(
            "SELECT id, sal, senha FROM perfil WHERE usuario=?", (usuario.casefold(),)
        ).fetchone()
    if linha and hmac.compare_digest(linha["senha"], hash_senha(senha, linha["sal"])):
        return linha["id"]
    return None


def conferir(senha, conta_id=1):
    with conexao() as banco:
        linha = banco.execute('SELECT sal,senha FROM perfil WHERE id=?', (conta_id,)).fetchone()
        return bool(linha and hmac.compare_digest(linha['senha'], hash_senha(senha, linha['sal'])))


def sessao_nova(conta_id):
    token = secrets.token_urlsafe(32)
    with conexao() as banco:
        banco.execute('DELETE FROM sessoes WHERE expira < ?', (time.time(),))
        banco.execute('INSERT INTO sessoes(token, expira, conta_id) VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), time.time()+604800, conta_id))
    return token


def conta_da_sessao(token):
    if not token:
        return None
    with conexao() as banco:
        linha = banco.execute('SELECT conta_id FROM sessoes WHERE token=? AND expira>?', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        return linha['conta_id'] if linha else None


def sair(token):
    with conexao() as banco:
        banco.execute('DELETE FROM sessoes WHERE token=?',(hashlib.sha256((token or '').encode()).hexdigest(),))


def alterar(nome, senha=None, conta_id=1):
    with conexao() as banco:
        banco.execute('UPDATE perfil SET nome=? WHERE id=?',(nome, conta_id))
        if senha:
            sal=secrets.token_hex(16)
            banco.execute('UPDATE perfil SET sal=?,senha=? WHERE id=?',(sal,hash_senha(senha,sal), conta_id))
            banco.execute('DELETE FROM sessoes WHERE conta_id=?', (conta_id,))


def listar_conversas(conta_id):
    with conexao() as banco:
        return [dict(r) for r in banco.execute('SELECT id,titulo,atualizado FROM conversas WHERE conta_id=? ORDER BY atualizado DESC', (conta_id,))]


def ler_conversa(identificador, conta_id):
    with conexao() as banco:
        r=banco.execute('SELECT * FROM conversas WHERE id=? AND conta_id=?',(identificador, conta_id)).fetchone()
        if not r:
            return None
        resultado=dict(r)
        for campo in ('mensagens','eventos','fontes'):
            resultado[campo]=json.loads(resultado[campo])
        return resultado


def salvar(identificador, mensagens, eventos, fontes, conta_id):
    with conexao() as banco:
        banco.execute("""
            INSERT INTO conversas(id, titulo, mensagens, eventos, fontes, atualizado, conta_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                mensagens=excluded.mensagens, eventos=excluded.eventos,
                fontes=excluded.fontes, atualizado=excluded.atualizado
            WHERE conversas.conta_id=excluded.conta_id
        """, (
            identificador, mensagens[0]['text'][:65], json.dumps(mensagens),
            json.dumps(eventos), json.dumps(fontes), time.time(), conta_id,
        ))
