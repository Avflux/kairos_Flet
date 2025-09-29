"""
Testes unitários para JSONDataProvider.

Este módulo contém testes abrangentes para a implementação do JSONDataProvider,
incluindo funcionalidades de salvamento, carregamento, observação de mudanças,
debouncing e versionamento de dados.
"""

import unittest
import tempfile
import os
import json
import time
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock, call

from services.web_server.data_provider import JSONDataProvider, JSONFileHandler
from services.web_server.exceptions import SincronizacaoError


class TestJSONDataProvider(unittest.TestCase):
    """Testes para a classe JSONDataProvider."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo_teste = os.path.join(self.temp_dir, "test_sync.json")
        
        # Criar provider com arquivo de teste
        self.provider = JSONDataProvider(self.arquivo_teste)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        # Parar observador se estiver ativo
        if hasattr(self.provider, '_observer') and self.provider._observer:
            self.provider.parar_observador()
        
        # Remover arquivos temporários
        if os.path.exists(self.arquivo_teste):
            os.remove(self.arquivo_teste)
        os.rmdir(self.temp_dir)
    
    def test_inicializacao_cria_arquivo_inicial(self):
        """Testa se a inicialização cria o arquivo inicial corretamente."""
        # Verificar se o arquivo foi criado
        self.assertTrue(os.path.exists(self.arquivo_teste))
        
        # Verificar conteúdo inicial
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        self.assertIn("timestamp", dados)
        self.assertIn("versao", dados)
        self.assertIn("dados", dados)
        self.assertEqual(dados["versao"], 1)
        self.assertEqual(dados["dados"], {})
    
    def test_inicializacao_com_arquivo_existente(self):
        """Testa inicialização quando o arquivo já existe."""
        # Criar arquivo com dados existentes
        dados_existentes = {
            "timestamp": "2023-01-01T00:00:00",
            "versao": 5,
            "dados": {"teste": "valor"}
        }
        
        with open(self.arquivo_teste, 'w', encoding='utf-8') as f:
            json.dump(dados_existentes, f)
        
        # Criar novo provider
        provider = JSONDataProvider(self.arquivo_teste)
        
        # Verificar que não sobrescreveu o arquivo
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        self.assertEqual(dados["versao"], 5)
        self.assertEqual(dados["dados"]["teste"], "valor")
    
    def test_salvar_dados_simples(self):
        """Testa salvamento de dados simples."""
        dados_teste = {
            "nome": "João",
            "idade": 30,
            "ativo": True
        }
        
        self.provider.salvar_dados(dados_teste)
        
        # Verificar se os dados foram salvos
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados_arquivo = json.load(f)
        
        self.assertEqual(dados_arquivo["dados"], dados_teste)
        self.assertGreater(dados_arquivo["versao"], 1)
        self.assertIn("timestamp", dados_arquivo)
    
    def test_salvar_dados_incrementa_versao(self):
        """Testa se salvar dados incrementa a versão corretamente."""
        # Primeira salvada
        self.provider.salvar_dados({"teste": 1})
        
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados1 = json.load(f)
        
        # Segunda salvada
        self.provider.salvar_dados({"teste": 2})
        
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados2 = json.load(f)
        
        self.assertEqual(dados2["versao"], dados1["versao"] + 1)
    
    def test_carregar_dados_arquivo_vazio(self):
        """Testa carregamento quando o arquivo não existe."""
        # Remover arquivo
        os.remove(self.arquivo_teste)
        
        dados = self.provider.carregar_dados()
        self.assertEqual(dados, {})
    
    def test_carregar_dados_com_conteudo(self):
        """Testa carregamento de dados com conteúdo."""
        dados_teste = {
            "usuario": "Maria",
            "configuracoes": {
                "tema": "escuro",
                "idioma": "pt-BR"
            }
        }
        
        self.provider.salvar_dados(dados_teste)
        dados_carregados = self.provider.carregar_dados()
        
        self.assertEqual(dados_carregados, dados_teste)
    
    def test_salvar_dados_com_erro_permissao(self):
        """Testa tratamento de erro quando não há permissão para escrever."""
        # Tornar o diretório somente leitura (apenas no Unix)
        if os.name != 'nt':  # Não é Windows
            os.chmod(self.temp_dir, 0o444)
            
            with self.assertRaises(SincronizacaoError) as context:
                self.provider.salvar_dados({"teste": "valor"})
            
            self.assertIn("Erro ao salvar dados JSON", str(context.exception))
            
            # Restaurar permissões
            os.chmod(self.temp_dir, 0o755)
    
    def test_carregar_dados_arquivo_corrompido(self):
        """Testa carregamento de arquivo JSON corrompido."""
        # Escrever JSON inválido
        with open(self.arquivo_teste, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")
        
        with self.assertRaises(SincronizacaoError) as context:
            self.provider.carregar_dados()
        
        self.assertIn("Erro ao carregar dados JSON", str(context.exception))
    
    def test_thread_safety_salvamento_concorrente(self):
        """Testa thread safety durante salvamentos concorrentes."""
        resultados = []
        erros = []
        
        def salvar_dados_thread(thread_id):
            try:
                for i in range(10):
                    dados = {f"thread_{thread_id}": f"valor_{i}"}
                    self.provider.salvar_dados(dados)
                    time.sleep(0.01)  # Pequena pausa para simular concorrência
                resultados.append(f"Thread {thread_id} concluída")
            except Exception as e:
                erros.append(f"Thread {thread_id}: {str(e)}")
        
        # Criar múltiplas threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=salvar_dados_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        self.assertEqual(len(erros), 0, f"Erros encontrados: {erros}")
        self.assertEqual(len(resultados), 3)
        
        # Verificar se o arquivo final é válido
        dados_finais = self.provider.carregar_dados()
        self.assertIsInstance(dados_finais, dict)


class TestJSONFileHandler(unittest.TestCase):
    """Testes para a classe JSONFileHandler."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo_teste = os.path.join(self.temp_dir, "test_handler.json")
        self.callback_chamado = False
        self.dados_callback = None
        
        # Criar arquivo inicial
        dados_iniciais = {"teste": "inicial"}
        with open(self.arquivo_teste, 'w', encoding='utf-8') as f:
            json.dump(dados_iniciais, f)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        if os.path.exists(self.arquivo_teste):
            os.remove(self.arquivo_teste)
        os.rmdir(self.temp_dir)
    
    def callback_teste(self, dados):
        """Callback de teste para verificar chamadas."""
        self.callback_chamado = True
        self.dados_callback = dados
    
    def test_callback_chamado_na_modificacao(self):
        """Testa se o callback é chamado quando o arquivo é modificado."""
        handler = JSONFileHandler(self.arquivo_teste, self.callback_teste)
        
        # Simular evento de modificação
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(self.arquivo_teste)
        
        handler.on_modified(event)
        
        # Aguardar debounce
        time.sleep(0.6)
        
        self.assertTrue(self.callback_chamado)
        self.assertIsNotNone(self.dados_callback)
    
    def test_debounce_multiplas_modificacoes(self):
        """Testa se o debouncing funciona com múltiplas modificações."""
        contador_callbacks = 0
        
        def callback_contador(dados):
            nonlocal contador_callbacks
            contador_callbacks += 1
        
        handler = JSONFileHandler(self.arquivo_teste, callback_contador)
        
        # Simular múltiplas modificações rápidas
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(self.arquivo_teste)
        
        for _ in range(5):
            handler.on_modified(event)
            time.sleep(0.1)  # Intervalo menor que o debounce
        
        # Aguardar debounce completo
        time.sleep(0.6)
        
        # Deve ter sido chamado apenas uma vez devido ao debounce
        self.assertEqual(contador_callbacks, 1)
    
    def test_ignora_eventos_de_diretorio(self):
        """Testa se eventos de diretório são ignorados."""
        handler = JSONFileHandler(self.arquivo_teste, self.callback_teste)
        
        # Simular evento de diretório
        from watchdog.events import DirModifiedEvent
        event = DirModifiedEvent(self.temp_dir)
        
        handler.on_modified(event)
        
        # Aguardar possível callback
        time.sleep(0.6)
        
        self.assertFalse(self.callback_chamado)
    
    def test_ignora_arquivos_diferentes(self):
        """Testa se arquivos diferentes são ignorados."""
        handler = JSONFileHandler(self.arquivo_teste, self.callback_teste)
        
        # Criar arquivo diferente
        arquivo_diferente = os.path.join(self.temp_dir, "outro_arquivo.json")
        with open(arquivo_diferente, 'w') as f:
            f.write("{}")
        
        # Simular evento no arquivo diferente
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(arquivo_diferente)
        
        handler.on_modified(event)
        
        # Aguardar possível callback
        time.sleep(0.6)
        
        self.assertFalse(self.callback_chamado)
        
        # Limpar
        os.remove(arquivo_diferente)


class TestJSONDataProviderObservador(unittest.TestCase):
    """Testes para funcionalidade de observador do JSONDataProvider."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo_teste = os.path.join(self.temp_dir, "test_observer.json")
        self.provider = JSONDataProvider(self.arquivo_teste)
        
        self.callback_chamado = False
        self.dados_recebidos = None
        self.contador_callbacks = 0
    
    def tearDown(self):
        """Limpeza após cada teste."""
        self.provider.parar_observador()
        if os.path.exists(self.arquivo_teste):
            os.remove(self.arquivo_teste)
        os.rmdir(self.temp_dir)
    
    def callback_teste(self, dados):
        """Callback de teste."""
        self.callback_chamado = True
        self.dados_recebidos = dados
        self.contador_callbacks += 1
    
    def test_configurar_observador(self):
        """Testa configuração do observador."""
        self.provider.configurar_observador(self.callback_teste)
        
        # Verificar se o observador foi configurado
        self.assertIsNotNone(self.provider._observer)
        self.assertIsNotNone(self.provider._handler)
        self.assertTrue(self.provider._observer.is_alive())
    
    def test_parar_observador(self):
        """Testa parada do observador."""
        self.provider.configurar_observador(self.callback_teste)
        
        # Parar observador
        self.provider.parar_observador()
        
        # Verificar se foi parado
        self.assertIsNone(self.provider._observer)
        self.assertIsNone(self.provider._handler)
    
    def test_reconfigurar_observador(self):
        """Testa reconfiguração do observador."""
        # Configurar primeiro observador
        self.provider.configurar_observador(self.callback_teste)
        primeiro_observer = self.provider._observer
        
        # Reconfigurar com novo callback
        def novo_callback(dados):
            pass
        
        self.provider.configurar_observador(novo_callback)
        
        # Verificar se o observador foi trocado
        self.assertIsNotNone(self.provider._observer)
        self.assertNotEqual(self.provider._observer, primeiro_observer)
    
    @patch('services.web_server.data_provider.Observer')
    def test_observador_com_mock(self, mock_observer_class):
        """Testa observador usando mock para controle total."""
        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer
        
        # Configurar observador
        self.provider.configurar_observador(self.callback_teste)
        
        # Verificar chamadas
        mock_observer_class.assert_called_once()
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()
        
        # Parar observador
        self.provider.parar_observador()
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()


class TestJSONDataProviderVersioamento(unittest.TestCase):
    """Testes para sistema de versionamento do JSONDataProvider."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo_teste = os.path.join(self.temp_dir, "test_versioning.json")
        self.provider = JSONDataProvider(self.arquivo_teste)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        if os.path.exists(self.arquivo_teste):
            os.remove(self.arquivo_teste)
        os.rmdir(self.temp_dir)
    
    def test_versao_inicial(self):
        """Testa se a versão inicial é 1."""
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        self.assertEqual(dados["versao"], 1)
    
    def test_incremento_versao_sequencial(self):
        """Testa incremento sequencial de versões."""
        versoes = []
        
        for i in range(5):
            self.provider.salvar_dados({"iteracao": i})
            
            with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            versoes.append(dados["versao"])
        
        # Verificar sequência crescente
        for i in range(1, len(versoes)):
            self.assertEqual(versoes[i], versoes[i-1] + 1)
    
    def test_preservacao_versao_existente(self):
        """Testa se versão existente é preservada ao carregar."""
        # Criar arquivo com versão específica
        dados_com_versao = {
            "timestamp": datetime.now().isoformat(),
            "versao": 42,
            "dados": {"teste": "valor"}
        }
        
        with open(self.arquivo_teste, 'w', encoding='utf-8') as f:
            json.dump(dados_com_versao, f)
        
        # Salvar novos dados
        self.provider.salvar_dados({"novo": "dado"})
        
        # Verificar se a versão foi incrementada a partir da existente
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        self.assertEqual(dados["versao"], 43)
    
    def test_timestamp_atualizado(self):
        """Testa se o timestamp é atualizado a cada salvamento."""
        # Primeiro salvamento
        timestamp_inicial = datetime.now()
        self.provider.salvar_dados({"teste": 1})
        
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados1 = json.load(f)
        
        # Aguardar um pouco
        time.sleep(0.1)
        
        # Segundo salvamento
        self.provider.salvar_dados({"teste": 2})
        
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            dados2 = json.load(f)
        
        # Verificar se timestamps são diferentes
        self.assertNotEqual(dados1["timestamp"], dados2["timestamp"])
        
        # Verificar se o segundo timestamp é posterior
        ts1 = datetime.fromisoformat(dados1["timestamp"])
        ts2 = datetime.fromisoformat(dados2["timestamp"])
        self.assertGreater(ts2, ts1)


class TestJSONDataProviderIntegracao(unittest.TestCase):
    """Testes de integração para JSONDataProvider."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.arquivo_teste = os.path.join(self.temp_dir, "test_integration.json")
        self.provider = JSONDataProvider(self.arquivo_teste)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        self.provider.parar_observador()
        if os.path.exists(self.arquivo_teste):
            os.remove(self.arquivo_teste)
        os.rmdir(self.temp_dir)
    
    def test_fluxo_completo_sincronizacao(self):
        """Testa fluxo completo de sincronização."""
        dados_recebidos = []
        
        def callback_coleta(dados):
            dados_recebidos.append(dados.copy())
        
        # Configurar observador
        self.provider.configurar_observador(callback_coleta)
        
        # Dados de teste
        dados_teste = {
            "usuario": "João",
            "configuracoes": {
                "tema": "claro",
                "notificacoes": True
            },
            "historico": [
                {"acao": "login", "timestamp": "2023-01-01T10:00:00"},
                {"acao": "logout", "timestamp": "2023-01-01T18:00:00"}
            ]
        }
        
        # Salvar dados
        self.provider.salvar_dados(dados_teste)
        
        # Carregar dados
        dados_carregados = self.provider.carregar_dados()
        
        # Verificar integridade
        self.assertEqual(dados_carregados, dados_teste)
        
        # Verificar estrutura do arquivo
        with open(self.arquivo_teste, 'r', encoding='utf-8') as f:
            estrutura_arquivo = json.load(f)
        
        self.assertIn("timestamp", estrutura_arquivo)
        self.assertIn("versao", estrutura_arquivo)
        self.assertIn("dados", estrutura_arquivo)
        self.assertEqual(estrutura_arquivo["dados"], dados_teste)
        self.assertGreater(estrutura_arquivo["versao"], 1)
    
    def test_performance_multiplos_salvamentos(self):
        """Testa performance com múltiplos salvamentos."""
        import time
        
        inicio = time.time()
        
        # Realizar múltiplos salvamentos
        for i in range(100):
            dados = {
                "iteracao": i,
                "dados_grandes": "x" * 1000,  # 1KB de dados
                "timestamp": datetime.now().isoformat()
            }
            self.provider.salvar_dados(dados)
        
        fim = time.time()
        tempo_total = fim - inicio
        
        # Verificar se não demorou muito (ajustar conforme necessário)
        self.assertLess(tempo_total, 5.0, "Salvamentos muito lentos")
        
        # Verificar integridade final
        dados_finais = self.provider.carregar_dados()
        self.assertEqual(dados_finais["iteracao"], 99)


if __name__ == '__main__':
    unittest.main()