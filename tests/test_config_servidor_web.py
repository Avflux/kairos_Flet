"""
Testes para o sistema de configuração do servidor web integrado.

Este módulo contém testes abrangentes para validar o funcionamento
do sistema de configuração, incluindo validação, carregamento de
arquivos JSON e funcionalidades de debug.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.web_server.config import (
    ConfiguracaoServidorWeb,
    ErroConfiguracaoServidorWeb,
    ErroValidacaoConfiguracao,
    ErroCarregamentoConfiguracao,
    NivelLog,
    obter_configuracao_padrao,
    carregar_configuracao_do_ambiente,
    criar_configuracao_exemplo
)
from services.web_server.config_manager import ConfigManager
from services.web_server.config_utils import (
    verificar_porta_disponivel,
    encontrar_porta_disponivel,
    validar_diretorio_html,
    validar_arquivo_index,
    diagnosticar_configuracao,
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao
)


class TestConfiguracaoServidorWeb(unittest.TestCase):
    """Testes para a classe ConfiguracaoServidorWeb."""
    
    def test_configuracao_padrao(self):
        """Testa criação de configuração com valores padrão."""
        config = ConfiguracaoServidorWeb()
        
        # Verificar valores padrão
        self.assertEqual(config.porta_preferencial, 8080)
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.diretorio_html, "web_content")
        self.assertTrue(config.cors_habilitado)
        self.assertFalse(config.modo_debug)
        self.assertEqual(config.nivel_log, "INFO")
    
    def test_validacao_portas_validas(self):
        """Testa validação com portas válidas."""
        config = ConfiguracaoServidorWeb(
            porta_preferencial=8080,
            porta_minima=8080,
            porta_maxima=8090
        )
        
        # Não deve lançar exceção
        config.validar()
    
    def test_validacao_porta_invalida(self):
        """Testa validação com porta inválida."""
        with self.assertRaises(ErroValidacaoConfiguracao):
            ConfiguracaoServidorWeb(porta_preferencial=100)  # Porta muito baixa
    
    def test_validacao_intervalo_portas_invalido(self):
        """Testa validação com intervalo de portas inválido."""
        with self.assertRaises(ErroValidacaoConfiguracao):
            ConfiguracaoServidorWeb(
                porta_minima=8090,
                porta_maxima=8080  # Mínima maior que máxima
            )
    
    def test_validacao_host_vazio(self):
        """Testa validação com host vazio."""
        with self.assertRaises(ErroValidacaoConfiguracao):
            ConfiguracaoServidorWeb(host="")
    
    def test_validacao_nivel_log_invalido(self):
        """Testa validação com nível de log inválido."""
        with self.assertRaises(ErroValidacaoConfiguracao):
            ConfiguracaoServidorWeb(nivel_log="INVALID")
    
    def test_validacao_timeout_invalido(self):
        """Testa validação com timeout inválido."""
        with self.assertRaises(ErroValidacaoConfiguracao):
            ConfiguracaoServidorWeb(timeout_servidor=0)
    
    def test_para_dict(self):
        """Testa conversão para dicionário."""
        config = ConfiguracaoServidorWeb()
        dados = config.para_dict()
        
        self.assertIsInstance(dados, dict)
        self.assertIn('porta_preferencial', dados)
        self.assertIn('host', dados)
        self.assertIn('modo_debug', dados)
    
    def test_salvar_e_carregar_arquivo(self):
        """Testa salvamento e carregamento de arquivo JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            arquivo_temp = f.name
        
        try:
            # Criar configuração personalizada
            config_original = ConfiguracaoServidorWeb(
                porta_preferencial=8085,
                porta_minima=8080,
                porta_maxima=8090,
                modo_debug=True,
                nivel_log="DEBUG"
            )
            
            # Salvar arquivo
            config_original.salvar_arquivo(arquivo_temp)
            
            # Carregar arquivo
            config_carregada = ConfiguracaoServidorWeb.carregar_arquivo(arquivo_temp)
            
            # Verificar se os valores foram preservados
            self.assertEqual(config_carregada.porta_preferencial, 8085)
            self.assertTrue(config_carregada.modo_debug)
            self.assertEqual(config_carregada.nivel_log, "DEBUG")
            
        finally:
            os.unlink(arquivo_temp)
    
    def test_carregar_arquivo_inexistente(self):
        """Testa carregamento de arquivo inexistente."""
        with self.assertRaises(ErroCarregamentoConfiguracao):
            ConfiguracaoServidorWeb.carregar_arquivo("arquivo_inexistente.json")
    
    def test_carregar_com_fallback(self):
        """Testa carregamento com fallback."""
        arquivo_inexistente = "config_inexistente.json"
        
        # Carregar com fallback (deve criar configuração padrão)
        config = ConfiguracaoServidorWeb.carregar_com_fallback(
            arquivo_inexistente, 
            criar_se_nao_existir=False
        )
        
        # Deve retornar configuração padrão
        self.assertEqual(config.porta_preferencial, 8080)
        self.assertFalse(config.modo_debug)


class TestConfigManager(unittest.TestCase):
    """Testes para o ConfigManager."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Limpeza após os testes."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_inicializacao_sem_arquivo(self):
        """Testa inicialização sem arquivo de configuração."""
        manager = ConfigManager(
            caminho_config=self.config_file,
            monitorar_mudancas=False
        )
        
        config = manager.obter_configuracao()
        self.assertIsInstance(config, ConfiguracaoServidorWeb)
        
        # Arquivo deve ter sido criado
        self.assertTrue(Path(self.config_file).exists())
    
    def test_atualizacao_configuracao(self):
        """Testa atualização de configuração."""
        manager = ConfigManager(
            caminho_config=self.config_file,
            monitorar_mudancas=False
        )
        
        # Atualizar configuração
        sucesso = manager.atualizar_configuracao(
            porta_preferencial=8085,
            porta_minima=8080,
            porta_maxima=8090,
            modo_debug=True
        )
        
        self.assertTrue(sucesso)
        
        # Verificar se foi atualizada
        config = manager.obter_configuracao()
        self.assertEqual(config.porta_preferencial, 8085)
        self.assertTrue(config.modo_debug)
    
    def test_callback_mudanca(self):
        """Testa callback de mudança de configuração."""
        callback_chamado = False
        nova_config = None
        
        def callback(config):
            nonlocal callback_chamado, nova_config
            callback_chamado = True
            nova_config = config
        
        manager = ConfigManager(
            caminho_config=self.config_file,
            monitorar_mudancas=False,
            callback_mudanca=callback
        )
        
        # Atualizar configuração
        manager.atualizar_configuracao(
            porta_preferencial=8085,
            porta_minima=8080,
            porta_maxima=8090
        )
        
        # Verificar se callback foi chamado
        self.assertTrue(callback_chamado)
        self.assertIsNotNone(nova_config)
        self.assertEqual(nova_config.porta_preferencial, 8085)


class TestConfigUtils(unittest.TestCase):
    """Testes para utilitários de configuração."""
    
    def test_verificar_porta_disponivel(self):
        """Testa verificação de porta disponível."""
        # Porta 80 provavelmente não está disponível para usuário comum
        # Porta alta provavelmente está disponível
        resultado = verificar_porta_disponivel(65000)
        self.assertIsInstance(resultado, bool)
    
    def test_encontrar_porta_disponivel(self):
        """Testa busca por porta disponível."""
        porta = encontrar_porta_disponivel(60000, 60010)
        
        if porta is not None:
            self.assertGreaterEqual(porta, 60000)
            self.assertLessEqual(porta, 60010)
    
    def test_validar_diretorio_html_inexistente(self):
        """Testa validação de diretório inexistente."""
        valido, erros = validar_diretorio_html("diretorio_inexistente")
        
        self.assertFalse(valido)
        self.assertGreater(len(erros), 0)
        self.assertIn("não existe", erros[0])
    
    def test_validar_diretorio_html_valido(self):
        """Testa validação de diretório válido."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Criar arquivo HTML no diretório
            html_file = os.path.join(temp_dir, "test.html")
            with open(html_file, 'w') as f:
                f.write("<html><body>Test</body></html>")
            
            valido, erros = validar_diretorio_html(temp_dir)
            
            self.assertTrue(valido)
            self.assertEqual(len(erros), 0)
    
    def test_validar_arquivo_index_valido(self):
        """Testa validação de arquivo index válido."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Criar arquivo index HTML
            index_file = os.path.join(temp_dir, "index.html")
            with open(index_file, 'w') as f:
                f.write("<html><head><title>Test</title></head><body>Test</body></html>")
            
            valido, erros = validar_arquivo_index(temp_dir, "index.html")
            
            self.assertTrue(valido)
            self.assertEqual(len(erros), 0)
    
    def test_diagnosticar_configuracao_valida(self):
        """Testa diagnóstico de configuração válida."""
        config = ConfiguracaoServidorWeb()
        diagnostico = diagnosticar_configuracao(config)
        
        self.assertIsInstance(diagnostico, dict)
        self.assertIn('configuracao_valida', diagnostico)
        self.assertIn('erros', diagnostico)
        self.assertIn('avisos', diagnostico)
        self.assertIn('informacoes', diagnostico)
    
    def test_criar_configuracao_desenvolvimento(self):
        """Testa criação de configuração para desenvolvimento."""
        config = criar_configuracao_desenvolvimento()
        
        self.assertTrue(config.modo_debug)
        self.assertEqual(config.nivel_log, "DEBUG")
        self.assertFalse(config.cache_habilitado)
    
    def test_criar_configuracao_producao(self):
        """Testa criação de configuração para produção."""
        config = criar_configuracao_producao()
        
        self.assertFalse(config.modo_debug)
        self.assertEqual(config.nivel_log, "WARNING")
        self.assertTrue(config.cache_habilitado)


class TestCarregamentoAmbiente(unittest.TestCase):
    """Testes para carregamento de configuração do ambiente."""
    
    def test_carregar_configuracao_do_ambiente(self):
        """Testa carregamento de configuração de variáveis de ambiente."""
        with patch.dict(os.environ, {
            'SERVIDOR_WEB_PORTA': '8085',
            'SERVIDOR_WEB_DEBUG': 'true',
            'SERVIDOR_WEB_HOST': 'example.com'
        }):
            config = carregar_configuracao_do_ambiente()
            
            self.assertEqual(config.porta_preferencial, 8085)
            self.assertTrue(config.modo_debug)
            self.assertEqual(config.host, 'example.com')


class TestNivelLog(unittest.TestCase):
    """Testes para enum NivelLog."""
    
    def test_niveis_log_validos(self):
        """Testa se todos os níveis de log são válidos."""
        niveis_esperados = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for nivel in niveis_esperados:
            self.assertIn(nivel, [n.value for n in NivelLog])
    
    def test_nivel_log_invalido(self):
        """Testa criação com nível de log inválido."""
        with self.assertRaises(ValueError):
            NivelLog("INVALID")


class TestExcecoesConfiguracao(unittest.TestCase):
    """Testes para exceções de configuração."""
    
    def test_erro_configuracao_base(self):
        """Testa exceção base de configuração."""
        erro = ErroConfiguracaoServidorWeb("Erro de teste")
        self.assertEqual(str(erro), "Erro de teste")
    
    def test_erro_validacao_configuracao(self):
        """Testa exceção de validação."""
        erro = ErroValidacaoConfiguracao("Erro de validação")
        self.assertEqual(str(erro), "Erro de validação")
        self.assertIsInstance(erro, ErroConfiguracaoServidorWeb)
    
    def test_erro_carregamento_configuracao(self):
        """Testa exceção de carregamento."""
        erro = ErroCarregamentoConfiguracao("Erro de carregamento")
        self.assertEqual(str(erro), "Erro de carregamento")
        self.assertIsInstance(erro, ErroConfiguracaoServidorWeb)


class TestFuncoesUtilitarias(unittest.TestCase):
    """Testes para funções utilitárias."""
    
    def test_obter_configuracao_padrao(self):
        """Testa obtenção de configuração padrão."""
        config = obter_configuracao_padrao()
        
        self.assertIsInstance(config, ConfiguracaoServidorWeb)
        self.assertEqual(config.porta_preferencial, 8080)
        self.assertFalse(config.modo_debug)
    
    def test_criar_configuracao_exemplo(self):
        """Testa criação de arquivo de configuração de exemplo."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            arquivo_temp = f.name
        
        try:
            criar_configuracao_exemplo(arquivo_temp)
            
            # Verificar se arquivo foi criado
            self.assertTrue(Path(arquivo_temp).exists())
            
            # Verificar se pode ser carregado
            config = ConfiguracaoServidorWeb.carregar_arquivo(arquivo_temp)
            self.assertIsInstance(config, ConfiguracaoServidorWeb)
            
        finally:
            os.unlink(arquivo_temp)


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()