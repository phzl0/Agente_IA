import tempfile
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import armazenamento as db
from api import app


class ContaPersistencia(unittest.TestCase):
    def setUp(self):
        self.pasta=tempfile.TemporaryDirectory()
        self.patch=patch.object(db,'BANCO',Path(self.pasta.name)/'teste.db')
        self.patch.start()
        self.cliente=TestClient(app)

    def tearDown(self):
        self.patch.stop()
        self.pasta.cleanup()

    def test_conta_senha_historico_e_logout(self):
        self.assertEqual(self.cliente.get('/api/conversas').status_code,401)
        r=self.cliente.post('/api/conta/configurar',json={'nome':'Teste','senha':'senha-teste-123'})
        self.assertEqual(r.status_code,200)
        self.assertIn('HttpOnly',r.headers['set-cookie'])
        self.assertTrue(self.cliente.get('/api/conta').json()['autenticado'])
        self.assertEqual(self.cliente.post('/api/conta/configurar',json={'nome':'teste','senha':'outra-senha'}).status_code,409)
        modelo=AsyncMock(return_value={'resposta':'Resposta geral','eventos':[],'fontes':[]})
        with patch('api.obter_chave',return_value='teste'),patch('api.responder',modelo):
            r=self.cliente.post('/api/chat',json={'mensagem':'O que é a Binance?'})
            self.assertEqual(r.status_code,200)
            identificador=r.json()['conversa_id']
            self.assertEqual(self.cliente.get('/api/conversas').json()[0]['id'],identificador)
            self.assertEqual(self.cliente.get('/api/conversas/'+identificador).json()['mensagens'][0]['text'],'O que é a Binance?')
        nova_conexao=TestClient(app)
        nova_conexao.post('/api/conta/entrar',json={'nome':'Teste','senha':'senha-teste-123'})
        self.assertEqual(len(nova_conexao.get('/api/conversas').json()),1)
        self.assertEqual(self.cliente.put('/api/perfil',json={'nome':'Novo','senha_atual':'errada','nova_senha':'senha-nova-123'}).status_code,403)
        self.assertEqual(self.cliente.put('/api/perfil',json={'nome':'Novo','senha_atual':'senha-teste-123','nova_senha':'senha-nova-123'}).status_code,200)
        self.assertEqual(nova_conexao.get('/api/conversas').status_code,401)
        self.assertFalse(db.conferir('senha-teste-123'))
        self.assertTrue(db.conferir('senha-nova-123'))
        self.cliente.post('/api/conta/sair')
        self.assertEqual(self.cliente.get('/api/conversas').status_code,401)

    def test_contas_isolam_conversas_e_sessoes(self):
        self.cliente.post('/api/conta/configurar', json={'nome':'Primeira','senha':'senha-primeira'})
        segunda = TestClient(app)
        self.assertEqual(segunda.post('/api/conta/configurar', json={
            'nome':'Segunda','senha':'senha-segunda',
        }).status_code, 200)
        resposta = {'resposta':'Ok','eventos':[],'fontes':[]}
        with patch('api.obter_chave', return_value='teste'), patch('api.responder', AsyncMock(return_value=resposta)):
            conversa = self.cliente.post('/api/chat', json={'mensagem':'Privada'}).json()['conversa_id']
            self.assertEqual(segunda.get('/api/conversas').json(), [])
            self.assertEqual(segunda.get(f'/api/conversas/{conversa}').status_code, 404)
            self.assertEqual(segunda.post('/api/chat', json={
                'mensagem':'Continuar','conversa_id':conversa,
            }).status_code, 404)
        self.cliente.put('/api/perfil', json={
            'nome':'Nome novo','senha_atual':'senha-primeira','nova_senha':'senha-alterada',
        })
        self.assertEqual(segunda.get('/api/conta').json()['nome'], 'Segunda')
        self.assertEqual(self.cliente.get('/api/conta').json()['usuario'], 'primeira')

    def test_migra_conta_e_conversa_existentes(self):
        sal = '01' * 16
        with sqlite3.connect(db.BANCO) as banco:
            banco.executescript("""
                CREATE TABLE perfil(id INTEGER PRIMARY KEY, nome TEXT, sal TEXT, senha TEXT);
                CREATE TABLE sessoes(token TEXT PRIMARY KEY, expira REAL);
                CREATE TABLE conversas(id TEXT PRIMARY KEY, titulo TEXT, mensagens TEXT, eventos TEXT, fontes TEXT, atualizado REAL);
                INSERT INTO conversas VALUES('antiga', 'Histórico', '[]', '[]', '[]', 1);
            """)
            banco.execute('INSERT INTO perfil VALUES(1,?,?,?)', ('Paulo', sal, db.hash_senha('senha-antiga', sal)))
        resposta = self.cliente.post('/api/conta/entrar', json={'nome':'Paulo','senha':'senha-antiga'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.cliente.get('/api/conversas').json()[0]['id'], 'antiga')
