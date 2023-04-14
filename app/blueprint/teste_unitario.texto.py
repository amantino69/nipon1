import unittest
from unittest.mock import MagicMock, patch
from utils import texto
from nameparser import HumanName
import shutil
import os


class TestTexto(unittest.TestCase):

    @patch("shutil.copyfile")
    @patch("os.startfile")
    def test_texto_success(self, os_startfile_mock, shutil_copyfile_mock):
        operadora = "operadoraTeste"
        hoje = "20220101"
        first_name = "Nome Sobrenome"
        demanda = "demandaTeste"
        situacao = "situaçãoExemplo"
        origem_excel_expected = "paste_prefixo_excel/20220101/operadoraTeste/Nome Sobrenome/demandaTeste/Nome Sobrenome.xlsx"
        destino_excel_expected = "paste_prefixo_fonte/fonte.xlsx"
        docx_path_expected = "paste_prefixo_pastas_word/20220101/operadoraTeste/Nome Sobrenome/demandaTeste/Nome Sobrenome.docx"

        result = texto(operadora, hoje, first_name, demanda, situacao)

        shutil_copyfile_mock.assert_called_once_with(origem_excel_expected, destino_excel_expected)
        os_startfile_mock.assert_called_once_with(docx_path_expected)
        self.assertEqual(result, "webui.responder")

    @patch("shutil.copyfile")
    @patch("os.startfile")
    def test_texto_exception(self, os_startfile_mock, shutil_copyfile_mock):
        shutil_copyfile_mock.side_effect = Exception("Erro ao copiar o arquivo")

        operadora = "operadoraTeste"
        hoje = "20220101"
        first_name = "Nome Sobrenome"
        demanda = "demandaTeste"
        situacao = "situaçãoExemplo"

        with self.assertRaises(Exception) as context:
            texto(operadora, hoje, first_name, demanda, situacao)

            self.assertTrue('Erro ao copiar o arquivo' in str(context.exception))


if __name__ == "__main__":
    unittest.main()

