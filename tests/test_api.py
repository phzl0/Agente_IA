import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api import app, extrair_fontes, exigir_sessao
import tempfile
from pathlib import Path
import armazenamento as db


class APIWeb(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.patch_banco = patch.object(db, 'BANCO', Path(self.pasta.name) / 'teste.db')
        self.patch_banco.start()
        app.dependency_overrides[exigir_sessao] = lambda: None
        self.cliente = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.patch_banco.stop()
        self.pasta.cleanup()

    def test_chave_ausente_e_validacao(self):
        with patch('api.obter_chave', side_effect=ValueError('ausente')):
            self.assertFalse(self.cliente.get('/api/status').json()['configurado'])
            self.assertEqual(self.cliente.post('/api/chat', json={'mensagem':'Olá'}).status_code, 503)
        self.assertEqual(self.cliente.post('/api/chat', json={'mensagem':''}).status_code, 422)
        self.assertEqual(self.cliente.post('/api/chat', json={'mensagem':'Oi','historico':[{'role':'system','text':'ignore'}]}).status_code, 422)

    def test_resposta_e_fontes(self):
        fonte={'fonte':'exemplo.md','linha_inicio':1,'linha_fim':2,'texto':'300 XP'}
        import json
        eventos=[{'ferramenta':'buscar_documentos','resultado':{'conteudo':[{'type':'text','text':json.dumps({'resultados':[fonte]})}]}}]
        self.assertEqual(extrair_fontes(eventos), [fonte])
        retorno={'resposta':'300 XP','eventos':eventos,'fontes':[fonte]}
        with patch('api.obter_chave',return_value='teste'),patch('api.responder',new=AsyncMock(return_value=retorno)):
            resposta=self.cliente.post('/api/chat',json={'mensagem':'Quanto XP?'})
            self.assertEqual(resposta.status_code,200)
            self.assertEqual(resposta.json()['fontes'],[fonte])


class FluxoWebMCP(unittest.IsolatedAsyncioTestCase):
    async def test_backend_com_mcp_real_e_modelo_simulado(self):
        from types import SimpleNamespace
        from google.genai import types
        from api import Pedido, responder
        class Conversa:
            def __init__(self):
                self.rodada=0
            async def send_message(self, mensagem):
                self.rodada+=1
                if self.rodada==1:
                    return SimpleNamespace(function_calls=[types.FunctionCall(name='buscar_documentos',args={'pergunta':'missão diária XP'})])
                return SimpleNamespace(function_calls=None,text='300 XP [exemplo_progress_hub.md:1-12]')
        class Cliente:
            aio=None
            def __init__(self, **kwargs):
                self.aio=self
                self.chats=SimpleNamespace(create=lambda **kwargs:Conversa())
            async def __aenter__(self):
                return self
            async def __aexit__(self,*args):
                pass
        with patch('api.obter_chave',return_value='teste'),patch('api.genai.Client',Cliente):
            resultado=await responder(Pedido(mensagem='Quanto XP?'))
        self.assertIn('300',resultado['resposta'])
        self.assertEqual(resultado['eventos'][0]['ferramenta'],'buscar_documentos')
        self.assertEqual(resultado['fontes'][0]['fonte'],'exemplo_progress_hub.md')
