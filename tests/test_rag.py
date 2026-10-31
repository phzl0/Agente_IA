import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rag


class BuscaDocumentos(unittest.TestCase):
    def test_fontes_atualizacao_e_ausencia(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            arquivo = raiz / "regras.md"
            arquivo.write_text("Missão diária concede 300 XP.", encoding="utf-8")
            (raiz / ".segredo.txt").write_text("senha confidencial")
            (raiz / "atalho.txt").symlink_to(arquivo)
            with patch.object(rag, "PASTA_DOCUMENTOS", raiz):
                resposta = rag.buscar_documentos("missao diaria")
                self.assertEqual(len(resposta["resultados"]), 1)
                self.assertEqual(resposta["resultados"][0]["fonte"], "regras.md")
                self.assertEqual(resposta["resultados"][0]["linha_inicio"], 1)
                self.assertFalse(rag.buscar_documentos("astronomia")["resultados"])
                self.assertFalse(rag.buscar_documentos("senha")["resultados"])
                arquivo.write_text("Missão diária concede 500 XP.", encoding="utf-8")
                self.assertIn("500", rag.buscar_documentos("missao")["resultados"][0]["texto"])
                self.assertFalse(rag.buscar_documentos("missao", 99)["resultados"])

    def test_trechos_limitados(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "grande.txt").write_text("missao " * 1000)
            with patch.object(rag, "PASTA_DOCUMENTOS", raiz):
                self.assertTrue(all(len(t["texto"]) <= 1800 for t in rag.indexar_documentos()))


if __name__ == "__main__":
    unittest.main()
