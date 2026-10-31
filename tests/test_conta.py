import tempfile
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
        self.assertEqual(self.cliente.post('/api/conta/configurar',json={'nome':'Outro','senha':'outra-senha'}).status_code,409)
        modelo=AsyncMock(return_value={'resposta':'Resposta geral','eventos':[],'fontes':[]})
        with patch('api.obter_chave',return_value='teste'),patch('api.responder',modelo):
            r=self.cliente.post('/api/chat',json={'mensagem':'O que é a Binance?'})
            self.assertEqual(r.status_code,200)
            identificador=r.json()['conversa_id']
            self.assertEqual(self.cliente.get('/api/conversas').json()[0]['id'],identificador)
            self.assertEqual(self.cliente.get('/api/conversas/'+identificador).json()['mensagens'][0]['text'],'O que é a Binance?')
        nova_conexao=TestClient(app)
        nova_conexao.post('/api/conta/entrar',json={'senha':'senha-teste-123'})
        self.assertEqual(len(nova_conexao.get('/api/conversas').json()),1)
        self.assertEqual(self.cliente.put('/api/perfil',json={'nome':'Novo','senha_atual':'errada','nova_senha':'senha-nova-123'}).status_code,403)
        self.assertEqual(self.cliente.put('/api/perfil',json={'nome':'Novo','senha_atual':'senha-teste-123','nova_senha':'senha-nova-123'}).status_code,200)
        self.assertEqual(nova_conexao.get('/api/conversas').status_code,401)
        self.assertFalse(db.conferir('senha-teste-123'))
        self.assertTrue(db.conferir('senha-nova-123'))
        self.cliente.post('/api/conta/sair')
        self.assertEqual(self.cliente.get('/api/conversas').status_code,401)
