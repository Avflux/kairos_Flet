"""
Factory para criação de provedores de dados.

Este módulo implementa o padrão Factory para seleção automática
entre diferentes tipos de provedores de dados (JSON/MySQL).
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging

from .data_provider import DataProvider
from .data_provider import JSONDataProvider
from .mysql_provider import MySQLDataProvider
from .config import ConfiguracaoMySQL
from .exceptions import SincronizacaoError


class TipoProvedor(Enum):
    """Tipos de provedores de dados disponíveis."""
    JSON = "json"
    MYSQL = "mysql"


class DataProviderFactory:
    """
    Factory para criação de provedores de dados.
    
    Implementa o padrão Factory Method para criar instâncias
    dos diferentes tipos de provedores de dados baseado na configuração.
    """
    
    def __init__(self):
        """Inicializa a factory."""
        self.logger = logging.getLogger(__name__)
        self._provedores_registrados = {
            TipoProvedor.JSON: self._criar_json_provider,
            TipoProvedor.MYSQL: self._criar_mysql_provider
        }
    
    def criar_provedor(
        self, 
        tipo: TipoProvedor, 
        configuracao: Dict[str, Any]
    ) -> DataProvider:
        """
        Cria um provedor de dados baseado no tipo especificado.
        
        Args:
            tipo: Tipo do provedor (JSON ou MySQL)
            configuracao: Configuração específica do provedor
            
        Returns:
            Instância do provedor de dados
            
        Raises:
            SincronizacaoError: Se tipo não for suportado ou configuração inválida
        """
        try:
            if tipo not in self._provedores_registrados:
                raise SincronizacaoError(f"Tipo de provedor não suportado: {tipo.value}")
            
            self.logger.info(f"Criando provedor de dados: {tipo.value}")
            
            criador = self._provedores_registrados[tipo]
            provedor = criador(configuracao)
            
            self.logger.info(f"Provedor {tipo.value} criado com sucesso")
            return provedor
            
        except Exception as e:
            erro_msg = f"Erro ao criar provedor {tipo.value}: {str(e)}"
            self.logger.error(erro_msg)
            raise SincronizacaoError(erro_msg)
    
    def criar_provedor_automatico(self, configuracao_geral: Dict[str, Any]) -> DataProvider:
        """
        Cria provedor automaticamente baseado na configuração.
        
        Args:
            configuracao_geral: Configuração geral do sistema
            
        Returns:
            Instância do provedor mais apropriado
        """
        try:
            # Determinar tipo baseado na configuração
            tipo_str = configuracao_geral.get("tipo_provedor", "json").lower()
            
            if tipo_str == "mysql":
                tipo = TipoProvedor.MYSQL
                config_provedor = configuracao_geral.get("mysql", {})
                
                # Validar configuração MySQL antes de tentar criar
                if not self.validar_configuracao(tipo, config_provedor):
                    raise SincronizacaoError("Configuração MySQL inválida")
            else:
                tipo = TipoProvedor.JSON
                config_provedor = configuracao_geral.get("json", {})
            
            self.logger.info(f"Seleção automática: usando provedor {tipo.value}")
            return self.criar_provedor(tipo, config_provedor)
            
        except Exception as e:
            # Fallback para JSON em caso de erro
            self.logger.warning(f"Erro na seleção automática, usando JSON: {str(e)}")
            return self.criar_provedor(TipoProvedor.JSON, {})
    
    def _criar_json_provider(self, configuracao: Dict[str, Any]) -> JSONDataProvider:
        """
        Cria provedor JSON.
        
        Args:
            configuracao: Configuração do provedor JSON
            
        Returns:
            Instância do JSONDataProvider
        """
        caminho_arquivo = configuracao.get("caminho_arquivo", "web_content/data/sync.json")
        
        return JSONDataProvider(arquivo_json=caminho_arquivo)
    
    def _criar_mysql_provider(self, configuracao: Dict[str, Any]) -> MySQLDataProvider:
        """
        Cria provedor MySQL.
        
        Args:
            configuracao: Configuração do provedor MySQL
            
        Returns:
            Instância do MySQLDataProvider
        """
        config_mysql = ConfiguracaoMySQL(
            host=configuracao.get("host", "localhost"),
            porta=configuracao.get("porta", 3306),
            usuario=configuracao.get("usuario", "root"),
            senha=configuracao.get("senha", ""),
            banco_dados=configuracao.get("banco_dados", "servidor_web_integrado"),
            charset=configuracao.get("charset", "utf8mb4"),
            timeout_conexao=configuracao.get("timeout_conexao", 30),
            pool_size=configuracao.get("pool_size", 5),
            max_overflow=configuracao.get("max_overflow", 10),
            ssl_habilitado=configuracao.get("ssl_habilitado", False),
            ssl_ca=configuracao.get("ssl_ca"),
            ssl_cert=configuracao.get("ssl_cert"),
            ssl_key=configuracao.get("ssl_key")
        )
        
        return MySQLDataProvider(config_mysql)
    
    def registrar_provedor(
        self, 
        tipo: TipoProvedor, 
        criador: callable
    ) -> None:
        """
        Registra um novo tipo de provedor.
        
        Args:
            tipo: Tipo do provedor
            criador: Função que cria o provedor
        """
        self._provedores_registrados[tipo] = criador
        self.logger.info(f"Provedor {tipo.value} registrado")
    
    def listar_provedores_disponiveis(self) -> list:
        """
        Lista todos os provedores disponíveis.
        
        Returns:
            Lista com os tipos de provedores disponíveis
        """
        return [tipo.value for tipo in self._provedores_registrados.keys()]
    
    def validar_configuracao(
        self, 
        tipo: TipoProvedor, 
        configuracao: Dict[str, Any]
    ) -> bool:
        """
        Valida configuração para um tipo de provedor.
        
        Args:
            tipo: Tipo do provedor
            configuracao: Configuração a ser validada
            
        Returns:
            True se configuração for válida
        """
        try:
            if tipo == TipoProvedor.JSON:
                return self._validar_config_json(configuracao)
            elif tipo == TipoProvedor.MYSQL:
                return self._validar_config_mysql(configuracao)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na validação de configuração: {str(e)}")
            return False
    
    def _validar_config_json(self, configuracao: Dict[str, Any]) -> bool:
        """Valida configuração JSON."""
        # Validações básicas para JSON
        caminho = configuracao.get("caminho_arquivo", "")
        if not isinstance(caminho, str):
            return False
        
        intervalo = configuracao.get("intervalo_observacao", 1.0)
        if not isinstance(intervalo, (int, float)) or intervalo <= 0:
            return False
        
        return True
    
    def _validar_config_mysql(self, configuracao: Dict[str, Any]) -> bool:
        """Valida configuração MySQL."""
        # Validações básicas para MySQL
        host = configuracao.get("host", "")
        if not isinstance(host, str) or not host:
            return False
        
        porta = configuracao.get("porta", 3306)
        if not isinstance(porta, int) or porta <= 0 or porta > 65535:
            return False
        
        usuario = configuracao.get("usuario", "")
        if not isinstance(usuario, str) or not usuario:
            return False
        
        return True


# Instância global da factory para uso conveniente
factory_provedor_dados = DataProviderFactory()


def criar_provedor_dados(configuracao: Dict[str, Any]) -> DataProvider:
    """
    Função de conveniência para criar provedor de dados.
    
    Args:
        configuracao: Configuração do sistema
        
    Returns:
        Instância do provedor de dados apropriado
    """
    return factory_provedor_dados.criar_provedor_automatico(configuracao)


def migrar_json_para_mysql(
    config_json: Dict[str, Any], 
    config_mysql: Dict[str, Any]
) -> None:
    """
    Utilitário para migrar dados de JSON para MySQL.
    
    Args:
        config_json: Configuração do provedor JSON
        config_mysql: Configuração do provedor MySQL
        
    Raises:
        SincronizacaoError: Se não conseguir realizar a migração
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info("Iniciando migração de JSON para MySQL")
        
        # Criar provedores
        provedor_json = factory_provedor_dados.criar_provedor(
            TipoProvedor.JSON, config_json
        )
        provedor_mysql = factory_provedor_dados.criar_provedor(
            TipoProvedor.MYSQL, config_mysql
        )
        
        # Carregar dados do JSON
        dados = provedor_json.carregar_dados()
        logger.info(f"Carregados {len(dados)} itens do JSON")
        
        # Criar estrutura MySQL
        provedor_mysql.criar_tabelas()
        
        # Salvar dados no MySQL
        provedor_mysql.salvar_dados(dados)
        logger.info("Dados migrados para MySQL com sucesso")
        
        # Verificar integridade
        dados_mysql = provedor_mysql.carregar_dados()
        if len(dados_mysql) == len(dados):
            logger.info("Migração verificada: dados íntegros")
        else:
            raise SincronizacaoError("Falha na verificação de integridade da migração")
            
    except Exception as e:
        erro_msg = f"Erro na migração JSON para MySQL: {str(e)}"
        logger.error(erro_msg)
        raise SincronizacaoError(erro_msg)