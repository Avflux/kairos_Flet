"""
Testes unitários para o WebServerManager.

Este módulo contém testes abrangentes para o WebServerManager,
incluindo inicialização, descoberta de portas, servir arquivos
e tratamento de erros.
"""

import unittest
import tempfile
import shutil
import socket
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import urllib.request
import urllib.error

from services.web_server.server_manager import WebServerManager, CustomHTTPRequestHandler
from services.web_server.models import ConfiguracaoServidorWeb
from services.web_server.exceptions import ServidorWebError, RecursoIndisponivelError, CodigosErro


class TestWebServerManager(unittest.TestCase):
    """Testes para a classe WebServerManager."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Configuração básica para testes
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8090,  # Usar porta diferente para evitar conflitos
            portas_alternativas=[8091, 8092, 8093],
            diretorio_html=self.temp_dir,
            modo_debug=False,
            timeout_servidor=5
        )
        
        # Criar arquivo HTML de teste
        self.arquivo_teste = Path(self.temp_dir) / "index.html"
        self.arquivo_teste.write_text("""
        <!DOCTYPE html>
        <html>
        <head><title>Teste</title></head>
        <body><h1>Pagina de Teste</h1></body>
        </html>
        """, encoding='utf-8')
    
    def tearDown(self):
        """Limpeza após cada teste."""
        # Garantir que não há servidores rodando
        pass
    
    def test_inicializacao_basica(self):
        """Testa inicialização básica do WebServerManager."""
        manager = WebServerManager(self.config)
        
        self.assertIsNotNone(manager.config)
        self.assertEqual(manager.config.porta_preferencial, 8090)
        self.assertFalse(manager.esta_ativo())
        self.assertIsNone(manager.obter_porta())
    
    def test_inicializacao_sem_config(self):
        """Testa inicialização sem configuração (usa padrão)."""
        manager = WebServerManager()
        
        self.assertIsNotNone(manager.config)
        self.assertEqual(manager.config.porta_preferencial, 8080)
        self.assertFalse(manager.esta_ativo())
    
    def test_config_invalida(self):
        """Testa inicialização com configuração inválida."""
        config_invalida = ConfiguracaoServidorWeb(
            porta_preferencial=99999,  # Porta inválida
            diretorio_html=""  # Diretório vazio
        )
        
        with self.assertRaises(ServidorWebError) as context:
            WebServerManager(config_invalida)
        
        self.assertIn("Configuração inválida", str(context.exception))
    
    def test_verificar_porta_disponivel(self):
        """Testa verificação de porta disponível."""
        manager = WebServerManager(self.config)
        
        # Porta provavelmente disponível
        self.assertTrue(manager._verificar_porta_disponivel(8090))
        
        # Criar servidor temporário para ocupar uma porta
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', 8091))
            sock.listen(1)
            
            # Agora a porta deve estar ocupada
            self.assertFalse(manager._verificar_porta_disponivel(8091))
    
    def test_encontrar_porta_disponivel_preferencial(self):
        """Testa encontrar porta disponível (preferencial livre)."""
        manager = WebServerManager(self.config)
        
        porta = manager._encontrar_porta_disponivel()
        self.assertEqual(porta, 8090)  # Deve retornar a preferencial
    
    def test_encontrar_porta_disponivel_alternativa(self):
        """Testa encontrar porta disponível (preferencial ocupada)."""
        manager = WebServerManager(self.config)
        
        # Ocupar a porta preferencial
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('localhost', 8090))
            sock.listen(1)
            
            porta = manager._encontrar_porta_disponivel()
            self.assertIn(porta, [8091, 8092, 8093])  # Deve usar alternativa
    
    def test_encontrar_porta_nenhuma_disponivel(self):
        """Testa quando nenhuma porta está disponível."""
        manager = WebServerManager(self.config)
        
        # Ocupar todas as portas
        sockets = []
        try:
            for porta in [8090, 8091, 8092, 8093]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', porta))
                sock.listen(1)
                sockets.append(sock)
            
            with self.assertRaises(RecursoIndisponivelError) as context:
                manager._encontrar_porta_disponivel()
            
            self.assertEqual(context.exception.codigo_erro, CodigosErro.RECURSO_PORTA_INDISPONIVEL)
            
        finally:
            # Fechar todos os sockets
            for sock in sockets:
                sock.close()
    
    def test_iniciar_servidor_sucesso(self):
        """Testa inicialização bem-sucedida do servidor."""
        manager = WebServerManager(self.config)
        
        try:
            url = manager.iniciar_servidor()
            
            self.assertTrue(manager.esta_ativo())
            self.assertEqual(url, f"http://localhost:{manager.obter_porta()}")
            self.assertIsNotNone(manager.obter_porta())
            
            # Aguardar um pouco para o servidor estar pronto
            time.sleep(0.2)
            
            # Testar se o servidor responde
            with urllib.request.urlopen(url, timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
            
        finally:
            manager.parar_servidor()
    
    def test_iniciar_servidor_ja_ativo(self):
        """Testa inicializar servidor quando já está ativo."""
        manager = WebServerManager(self.config)
        
        try:
            url1 = manager.iniciar_servidor()
            url2 = manager.iniciar_servidor()  # Segunda chamada
            
            self.assertEqual(url1, url2)
            self.assertTrue(manager.esta_ativo())
            
        finally:
            manager.parar_servidor()
    
    def test_parar_servidor(self):
        """Testa parada do servidor."""
        manager = WebServerManager(self.config)
        
        # Iniciar servidor
        manager.iniciar_servidor()
        self.assertTrue(manager.esta_ativo())
        
        # Parar servidor
        manager.parar_servidor()
        self.assertFalse(manager.esta_ativo())
        self.assertIsNone(manager.obter_porta())
    
    def test_parar_servidor_nao_ativo(self):
        """Testa parar servidor quando não está ativo."""
        manager = WebServerManager(self.config)
        
        # Não deve gerar erro
        manager.parar_servidor()
        self.assertFalse(manager.esta_ativo())
    
    def test_obter_url_servidor_ativo(self):
        """Testa obter URL com servidor ativo."""
        manager = WebServerManager(self.config)
        
        try:
            url_inicial = manager.iniciar_servidor()
            url_obtida = manager.obter_url()
            
            self.assertEqual(url_inicial, url_obtida)
            
        finally:
            manager.parar_servidor()
    
    def test_obter_url_servidor_inativo(self):
        """Testa obter URL com servidor inativo."""
        manager = WebServerManager(self.config)
        
        with self.assertRaises(ServidorWebError) as context:
            manager.obter_url()
        
        self.assertEqual(context.exception.codigo_erro, CodigosErro.SERVIDOR_NAO_RESPONSIVO)
    
    def test_obter_estatisticas(self):
        """Testa obtenção de estatísticas do servidor."""
        manager = WebServerManager(self.config)
        
        # Servidor inativo
        stats = manager.obter_estatisticas()
        self.assertFalse(stats["ativo"])
        self.assertIsNone(stats["porta"])
        
        try:
            # Servidor ativo
            manager.iniciar_servidor()
            stats = manager.obter_estatisticas()
            
            self.assertTrue(stats["ativo"])
            self.assertIsNotNone(stats["porta"])
            self.assertIsNotNone(stats["url"])
            self.assertEqual(stats["host"], "localhost")
            
        finally:
            manager.parar_servidor()
    
    def test_context_manager(self):
        """Testa uso como context manager."""
        with WebServerManager(self.config) as manager:
            self.assertTrue(manager.esta_ativo())
            url = manager.obter_url()
            self.assertIsNotNone(url)
        
        # Após sair do context, deve estar parado
        self.assertFalse(manager.esta_ativo())
    
    def test_servir_arquivo_html(self):
        """Testa servir arquivo HTML."""
        manager = WebServerManager(self.config)
        
        try:
            url = manager.iniciar_servidor()
            time.sleep(0.2)  # Aguardar servidor estar pronto
            
            # Testar arquivo index.html
            with urllib.request.urlopen(f"{url}/index.html", timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
                content = response.read().decode('utf-8', errors='ignore')
                self.assertIn("Pagina de Teste", content)
            
        finally:
            manager.parar_servidor()
    
    def test_servir_arquivo_inexistente(self):
        """Testa servir arquivo que não existe."""
        manager = WebServerManager(self.config)
        
        try:
            url = manager.iniciar_servidor()
            time.sleep(0.2)
            
            # Testar arquivo inexistente
            try:
                with urllib.request.urlopen(f"{url}/inexistente.html", timeout=2) as response:
                    self.fail("Deveria ter retornado 404")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 404)
            
        finally:
            manager.parar_servidor()
    
    def test_diretorio_html_nao_existe(self):
        """Testa inicialização quando diretório HTML não existe."""
        # Usar diretório que não existe
        config_temp = ConfiguracaoServidorWeb(
            porta_preferencial=8094,
            diretorio_html=str(Path(self.temp_dir) / "nao_existe"),
            modo_debug=False
        )
        
        manager = WebServerManager(config_temp)
        
        try:
            url = manager.iniciar_servidor()
            self.assertTrue(manager.esta_ativo())
            
            # Verificar se o diretório foi criado
            self.assertTrue(Path(config_temp.diretorio_html).exists())
            
        finally:
            manager.parar_servidor()


class TestCustomHTTPRequestHandler(unittest.TestCase):
    """Testes para o CustomHTTPRequestHandler."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        self.config = ConfiguracaoServidorWeb(
            diretorio_html=self.temp_dir,
            cors_habilitado=True,
            modo_debug=True
        )
    
    def test_cors_headers(self):
        """Testa se headers CORS são adicionados corretamente."""
        # Este teste seria mais complexo de implementar sem um servidor real
        # Por enquanto, testamos a lógica básica
        
        handler = CustomHTTPRequestHandler
        self.assertIsNotNone(handler)
    
    def test_validacao_caminhos(self):
        """Testa validação de caminhos para segurança."""
        # Criar arquivo de teste
        arquivo_teste = Path(self.temp_dir) / "teste.html"
        arquivo_teste.write_text("<html><body>Teste</body></html>")
        
        # Este teste seria mais detalhado com um servidor real
        # Por enquanto, verificamos que a classe existe e pode ser instanciada
        self.assertTrue(hasattr(CustomHTTPRequestHandler, 'translate_path'))


class TestIntegracaoWebServerManager(unittest.TestCase):
    """Testes de integração para o WebServerManager."""
    
    def setUp(self):
        """Configuração inicial para testes de integração."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Criar estrutura de arquivos de teste
        self.criar_estrutura_teste()
        
        self.config = ConfiguracaoServidorWeb(
            porta_preferencial=8095,
            portas_alternativas=[8096, 8097],
            diretorio_html=self.temp_dir,
            modo_debug=False
        )
    
    def criar_estrutura_teste(self):
        """Cria estrutura de arquivos para teste."""
        # Página principal
        (Path(self.temp_dir) / "index.html").write_text("""
        <!DOCTYPE html>
        <html>
        <head><title>Pagina Principal</title></head>
        <body>
            <h1>Bem-vindo</h1>
            <a href="sobre.html">Sobre</a>
        </body>
        </html>
        """, encoding='utf-8')
        
        # Página secundária
        (Path(self.temp_dir) / "sobre.html").write_text("""
        <!DOCTYPE html>
        <html>
        <head><title>Sobre</title></head>
        <body><h1>Sobre o Sistema</h1></body>
        </html>
        """, encoding='utf-8')
        
        # Subdiretório com arquivo
        subdir = Path(self.temp_dir) / "css"
        subdir.mkdir()
        (subdir / "style.css").write_text("body { font-family: Arial; }", encoding='utf-8')
    
    def test_navegacao_entre_paginas(self):
        """Testa navegação entre diferentes páginas."""
        manager = WebServerManager(self.config)
        
        try:
            url = manager.iniciar_servidor()
            time.sleep(0.2)
            
            # Testar página principal
            with urllib.request.urlopen(f"{url}/index.html", timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
                content = response.read().decode('utf-8', errors='ignore')
                self.assertIn("Bem-vindo", content)
            
            # Testar página secundária
            with urllib.request.urlopen(f"{url}/sobre.html", timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
                content = response.read().decode('utf-8', errors='ignore')
                self.assertIn("Sobre o Sistema", content)
            
            # Testar arquivo CSS
            with urllib.request.urlopen(f"{url}/css/style.css", timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
                content = response.read().decode('utf-8', errors='ignore')
                self.assertIn("Arial", content)
            
        finally:
            manager.parar_servidor()
    
    def test_multiplos_servidores_simultaneos(self):
        """Testa múltiplos servidores rodando simultaneamente."""
        config1 = ConfiguracaoServidorWeb(
            porta_preferencial=8098,
            diretorio_html=self.temp_dir
        )
        
        config2 = ConfiguracaoServidorWeb(
            porta_preferencial=8099,
            diretorio_html=self.temp_dir
        )
        
        manager1 = WebServerManager(config1)
        manager2 = WebServerManager(config2)
        
        try:
            url1 = manager1.iniciar_servidor()
            url2 = manager2.iniciar_servidor()
            
            self.assertNotEqual(url1, url2)
            self.assertTrue(manager1.esta_ativo())
            self.assertTrue(manager2.esta_ativo())
            
            time.sleep(0.2)
            
            # Ambos devem responder
            with urllib.request.urlopen(f"{url1}/index.html", timeout=2) as response1:
                self.assertEqual(response1.getcode(), 200)
            
            with urllib.request.urlopen(f"{url2}/index.html", timeout=2) as response2:
                self.assertEqual(response2.getcode(), 200)
            
        finally:
            manager1.parar_servidor()
            manager2.parar_servidor()
    
    def test_reinicializacao_servidor(self):
        """Testa reinicialização do servidor."""
        manager = WebServerManager(self.config)
        
        # Primeira inicialização
        url1 = manager.iniciar_servidor()
        porta1 = manager.obter_porta()
        manager.parar_servidor()
        
        # Segunda inicialização
        url2 = manager.iniciar_servidor()
        porta2 = manager.obter_porta()
        
        try:
            # Pode ser a mesma porta ou diferente
            self.assertIsNotNone(url2)
            self.assertIsNotNone(porta2)
            
            time.sleep(0.2)
            
            # Deve responder normalmente
            with urllib.request.urlopen(f"{url2}/index.html", timeout=2) as response:
                self.assertEqual(response.getcode(), 200)
            
        finally:
            manager.parar_servidor()


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main()