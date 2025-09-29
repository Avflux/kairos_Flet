"""
Módulo de configuração para o servidor web integrado.

Este módulo fornece classes e funções para gerenciar configurações
do servidor web, incluindo validação, carregamento de arquivos JSON
e configurações de segurança.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class NivelLog(Enum):
    """Níveis de log disponíveis."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErroConfiguracaoServidorWeb(Exception):
    """Exceção base para erros de configuração do servidor web."""
    pass


class ErroValidacaoConfiguracao(ErroConfiguracaoServidorWeb):
    """Erro de validação de configuração."""
    pass


class ErroCarregamentoConfiguracao(ErroConfiguracaoServidorWeb):
    """Erro no carregamento de arquivo de configuração."""
    pass


class TipoProvedor(Enum):
    """Tipos de provedores de dados disponíveis."""
    JSON = "json"
    MYSQL = "mysql"


@dataclass
class ConfiguracaoMySQL:
    """
    Configuração para conexão MySQL.
    
    Esta classe centraliza todas as configurações necessárias para
    conectar e operar com banco de dados MySQL.
    """
    
    # Configurações básicas de conexão
    host: str = "localhost"
    porta: int = 3306
    usuario: str = "root"
    senha: str = ""
    banco_dados: str = "servidor_web_integrado"
    charset: str = "utf8mb4"
    
    # Configurações de conexão avançadas
    timeout_conexao: int = 30
    timeout_leitura: int = 30
    timeout_escrita: int = 30
    
    # Configurações de pool de conexões
    pool_habilitado: bool = True
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # segundos
    
    # Configurações SSL
    ssl_habilitado: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_verificar_cert: bool = True
    
    # Configurações de retry e recuperação
    max_tentativas_reconexao: int = 3
    delay_reconexao: float = 1.0
    auto_commit: bool = True
    
    # Configurações de performance
    cache_consultas: bool = True
    cache_tamanho: int = 1000
    usar_unicode: bool = True
    
    def validar(self) -> None:
        """
        Valida as configurações MySQL.
        
        Raises:
            ErroValidacaoConfiguracao: Se alguma configuração for inválida
        """
        erros = []
        
        # Validar host
        if not self.host or not isinstance(self.host, str):
            erros.append("Host MySQL deve ser uma string não vazia")
        
        # Validar porta
        if not (1 <= self.porta <= 65535):
            erros.append("Porta MySQL deve estar entre 1 e 65535")
        
        # Validar usuário
        if not self.usuario or not isinstance(self.usuario, str):
            erros.append("Usuário MySQL deve ser uma string não vazia")
        
        # Validar banco de dados
        if not self.banco_dados or not isinstance(self.banco_dados, str):
            erros.append("Nome do banco de dados deve ser uma string não vazia")
        
        # Validar timeouts
        if self.timeout_conexao <= 0:
            erros.append("Timeout de conexão deve ser maior que zero")
        
        if self.timeout_leitura <= 0:
            erros.append("Timeout de leitura deve ser maior que zero")
        
        if self.timeout_escrita <= 0:
            erros.append("Timeout de escrita deve ser maior que zero")
        
        # Validar configurações de pool
        if self.pool_size <= 0:
            erros.append("Tamanho do pool deve ser maior que zero")
        
        if self.max_overflow < 0:
            erros.append("Max overflow não pode ser negativo")
        
        if self.pool_timeout <= 0:
            erros.append("Pool timeout deve ser maior que zero")
        
        # Validar SSL
        if self.ssl_habilitado:
            if self.ssl_ca and not os.path.exists(self.ssl_ca):
                erros.append(f"Arquivo SSL CA não encontrado: {self.ssl_ca}")
            
            if self.ssl_cert and not os.path.exists(self.ssl_cert):
                erros.append(f"Arquivo SSL cert não encontrado: {self.ssl_cert}")
            
            if self.ssl_key and not os.path.exists(self.ssl_key):
                erros.append(f"Arquivo SSL key não encontrado: {self.ssl_key}")
        
        # Validar configurações de retry
        if self.max_tentativas_reconexao <= 0:
            erros.append("Máximo de tentativas de reconexão deve ser maior que zero")
        
        if self.delay_reconexao < 0:
            erros.append("Delay de reconexão não pode ser negativo")
        
        if erros:
            raise ErroValidacaoConfiguracao(
                f"Erros de validação MySQL encontrados:\n" + "\n".join(f"- {erro}" for erro in erros)
            )
    
    def obter_url_conexao(self, incluir_senha: bool = False) -> str:
        """
        Gera URL de conexão MySQL.
        
        Args:
            incluir_senha: Se deve incluir senha na URL
            
        Returns:
            URL de conexão MySQL
        """
        senha_parte = f":{self.senha}" if incluir_senha and self.senha else ""
        return f"mysql://{self.usuario}{senha_parte}@{self.host}:{self.porta}/{self.banco_dados}"
    
    def para_dict(self) -> Dict[str, Any]:
        """
        Converte configuração MySQL para dicionário.
        
        Returns:
            Dicionário com configurações MySQL
        """
        return asdict(self)


@dataclass
class ConfiguracaoServidorWeb:
    """
    Configuração completa do servidor web integrado.
    
    Esta classe centraliza todas as configurações necessárias para
    o funcionamento do servidor web, incluindo parâmetros de rede,
    segurança, logging e diretórios.
    """
    
    # Configurações básicas do servidor
    porta_preferencial: int = 8080
    porta_minima: int = 8080
    porta_maxima: int = 8090
    host: str = "localhost"
    timeout_servidor: int = 30
    
    # Configurações de diretórios
    diretorio_html: str = "web_content"
    diretorio_dados: str = "web_content/data"
    arquivo_index: str = "index.html"
    
    # Configurações de CORS
    cors_habilitado: bool = True
    cors_origens: List[str] = field(default_factory=lambda: ["*"])
    cors_metodos: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_cabecalhos: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    cors_credenciais: bool = False
    
    # Configurações de segurança
    validar_caminhos: bool = True
    permitir_directory_listing: bool = False
    max_tamanho_upload: int = 10 * 1024 * 1024  # 10MB
    tipos_arquivo_permitidos: List[str] = field(default_factory=lambda: [
        ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"
    ])
    
    # Configurações de logging
    modo_debug: bool = False
    nivel_log: str = "INFO"
    arquivo_log: Optional[str] = None
    log_formato: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_rotacao: bool = True
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Configurações de sincronização
    intervalo_sincronizacao: float = 1.0  # segundos
    debounce_delay: float = 0.5  # segundos
    max_tentativas_retry: int = 3
    delay_retry: float = 1.0  # segundos
    
    # Configurações avançadas
    cache_habilitado: bool = True
    cache_max_age: int = 3600  # segundos
    compressao_habilitada: bool = True
    keep_alive: bool = True
    
    # Configurações de provedor de dados
    tipo_provedor: str = "json"  # "json" ou "mysql"
    configuracao_mysql: Optional[ConfiguracaoMySQL] = None
    
    # Configurações específicas do provedor JSON
    caminho_arquivo_json: str = "web_content/data/sync.json"
    
    # Configurações de migração
    backup_antes_migracao: bool = True
    diretorio_backup: str = "data/backup"
    
    def __post_init__(self):
        """Validação automática após inicialização."""
        self.validar()
    
    def validar(self) -> None:
        """
        Valida todas as configurações.
        
        Raises:
            ErroValidacaoConfiguracao: Se alguma configuração for inválida
        """
        erros = []
        
        # Validar portas
        if not (1024 <= self.porta_preferencial <= 65535):
            erros.append("Porta preferencial deve estar entre 1024 e 65535")
        
        if not (1024 <= self.porta_minima <= 65535):
            erros.append("Porta mínima deve estar entre 1024 e 65535")
            
        if not (1024 <= self.porta_maxima <= 65535):
            erros.append("Porta máxima deve estar entre 1024 e 65535")
            
        if self.porta_minima > self.porta_maxima:
            erros.append("Porta mínima não pode ser maior que porta máxima")
            
        if not (self.porta_minima <= self.porta_preferencial <= self.porta_maxima):
            erros.append("Porta preferencial deve estar entre porta mínima e máxima")
        
        # Validar host
        if not self.host or not isinstance(self.host, str):
            erros.append("Host deve ser uma string não vazia")
        
        # Validar timeout
        if self.timeout_servidor <= 0:
            erros.append("Timeout do servidor deve ser maior que zero")
        
        # Validar diretórios
        if not self.diretorio_html:
            erros.append("Diretório HTML não pode estar vazio")
            
        if not self.diretorio_dados:
            erros.append("Diretório de dados não pode estar vazio")
            
        if not self.arquivo_index:
            erros.append("Arquivo index não pode estar vazio")
        
        # Validar CORS
        if not isinstance(self.cors_origens, list):
            erros.append("CORS origens deve ser uma lista")
            
        if not isinstance(self.cors_metodos, list):
            erros.append("CORS métodos deve ser uma lista")
            
        if not isinstance(self.cors_cabecalhos, list):
            erros.append("CORS cabeçalhos deve ser uma lista")
        
        # Validar configurações de segurança
        if self.max_tamanho_upload <= 0:
            erros.append("Tamanho máximo de upload deve ser maior que zero")
            
        if not isinstance(self.tipos_arquivo_permitidos, list):
            erros.append("Tipos de arquivo permitidos deve ser uma lista")
        
        # Validar nível de log
        try:
            NivelLog(self.nivel_log.upper())
        except ValueError:
            erros.append(f"Nível de log inválido: {self.nivel_log}. "
                        f"Valores válidos: {[n.value for n in NivelLog]}")
        
        # Validar configurações de sincronização
        if self.intervalo_sincronizacao <= 0:
            erros.append("Intervalo de sincronização deve ser maior que zero")
            
        if self.debounce_delay < 0:
            erros.append("Delay de debounce não pode ser negativo")
            
        if self.max_tentativas_retry <= 0:
            erros.append("Máximo de tentativas de retry deve ser maior que zero")
            
        if self.delay_retry < 0:
            erros.append("Delay de retry não pode ser negativo")
        
        # Validar configurações de cache
        if self.cache_max_age < 0:
            erros.append("Cache max age não pode ser negativo")
        
        # Validar tipo de provedor
        if self.tipo_provedor not in ["json", "mysql"]:
            erros.append(f"Tipo de provedor inválido: {self.tipo_provedor}. Valores válidos: json, mysql")
        
        # Validar configuração MySQL se necessário
        if self.tipo_provedor == "mysql":
            if self.configuracao_mysql is None:
                erros.append("Configuração MySQL é obrigatória quando tipo_provedor é 'mysql'")
            else:
                try:
                    self.configuracao_mysql.validar()
                except ErroValidacaoConfiguracao as e:
                    erros.append(f"Erro na configuração MySQL: {e}")
        
        # Validar configurações de arquivo JSON
        if self.tipo_provedor == "json":
            if not self.caminho_arquivo_json:
                erros.append("Caminho do arquivo JSON não pode estar vazio")
        
        # Validar configurações de backup
        if not self.diretorio_backup:
            erros.append("Diretório de backup não pode estar vazio")
        
        if erros:
            raise ErroValidacaoConfiguracao(
                f"Erros de validação encontrados:\n" + "\n".join(f"- {erro}" for erro in erros)
            )
    
    def para_dict(self) -> Dict[str, Any]:
        """
        Converte a configuração para dicionário.
        
        Returns:
            Dicionário com todas as configurações
        """
        return asdict(self)
    
    def salvar_arquivo(self, caminho: Union[str, Path]) -> None:
        """
        Salva a configuração em um arquivo JSON.
        
        Args:
            caminho: Caminho do arquivo para salvar
            
        Raises:
            ErroCarregamentoConfiguracao: Se não conseguir salvar o arquivo
        """
        try:
            caminho = Path(caminho)
            caminho.parent.mkdir(parents=True, exist_ok=True)
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(self.para_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise ErroCarregamentoConfiguracao(
                f"Erro ao salvar configuração no arquivo {caminho}: {e}"
            )
    
    @classmethod
    def carregar_arquivo(cls, caminho: Union[str, Path]) -> 'ConfiguracaoServidorWeb':
        """
        Carrega configuração de um arquivo JSON.
        
        Args:
            caminho: Caminho do arquivo para carregar
            
        Returns:
            Instância de ConfiguracaoServidorWeb
            
        Raises:
            ErroCarregamentoConfiguracao: Se não conseguir carregar o arquivo
        """
        try:
            caminho = Path(caminho)
            
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho}")
            
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            return cls(**dados)
            
        except json.JSONDecodeError as e:
            raise ErroCarregamentoConfiguracao(
                f"Erro ao decodificar JSON do arquivo {caminho}: {e}"
            )
        except TypeError as e:
            raise ErroCarregamentoConfiguracao(
                f"Erro nos parâmetros de configuração do arquivo {caminho}: {e}"
            )
        except Exception as e:
            raise ErroCarregamentoConfiguracao(
                f"Erro ao carregar configuração do arquivo {caminho}: {e}"
            )
    
    @classmethod
    def carregar_com_fallback(
        cls, 
        caminho: Union[str, Path], 
        criar_se_nao_existir: bool = True
    ) -> 'ConfiguracaoServidorWeb':
        """
        Carrega configuração com fallback para configuração padrão.
        
        Args:
            caminho: Caminho do arquivo de configuração
            criar_se_nao_existir: Se deve criar arquivo com configuração padrão
            
        Returns:
            Instância de ConfiguracaoServidorWeb
        """
        try:
            return cls.carregar_arquivo(caminho)
        except ErroCarregamentoConfiguracao:
            # Se não conseguir carregar, usar configuração padrão
            config = cls()
            
            if criar_se_nao_existir:
                try:
                    config.salvar_arquivo(caminho)
                except ErroCarregamentoConfiguracao:
                    # Se não conseguir salvar, apenas usar configuração padrão
                    pass
            
            return config
    
    def configurar_logging(self) -> None:
        """
        Configura o sistema de logging baseado nas configurações.
        """
        # Configurar nível de log
        nivel = getattr(logging, self.nivel_log.upper(), logging.INFO)
        
        # Configurar formatador
        formatter = logging.Formatter(
            self.log_formato,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configurar logger principal
        logger = logging.getLogger('servidor_web_integrado')
        logger.setLevel(nivel)
        
        # Remover handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Adicionar handler de console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Adicionar handler de arquivo se especificado
        if self.arquivo_log:
            try:
                if self.log_rotacao:
                    from logging.handlers import RotatingFileHandler
                    file_handler = RotatingFileHandler(
                        self.arquivo_log,
                        maxBytes=self.log_max_bytes,
                        backupCount=self.log_backup_count,
                        encoding='utf-8'
                    )
                else:
                    file_handler = logging.FileHandler(
                        self.arquivo_log,
                        encoding='utf-8'
                    )
                
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
            except Exception as e:
                logger.warning(f"Não foi possível configurar log em arquivo: {e}")
        
        # Log de inicialização
        if self.modo_debug:
            logger.debug("Sistema de logging configurado com sucesso")
            logger.debug(f"Nível de log: {self.nivel_log}")
            logger.debug(f"Modo debug: {self.modo_debug}")


def obter_configuracao_padrao() -> ConfiguracaoServidorWeb:
    """
    Obtém uma instância da configuração padrão.
    
    Returns:
        ConfiguracaoServidorWeb com valores padrão
    """
    return ConfiguracaoServidorWeb()


def carregar_configuracao_do_ambiente() -> ConfiguracaoServidorWeb:
    """
    Carrega configuração a partir de variáveis de ambiente.
    
    Returns:
        ConfiguracaoServidorWeb com valores das variáveis de ambiente
    """
    config = ConfiguracaoServidorWeb()
    
    # Mapear variáveis de ambiente para atributos
    mapeamento_env = {
        'SERVIDOR_WEB_PORTA': 'porta_preferencial',
        'SERVIDOR_WEB_HOST': 'host',
        'SERVIDOR_WEB_DEBUG': 'modo_debug',
        'SERVIDOR_WEB_DIRETORIO_HTML': 'diretorio_html',
        'SERVIDOR_WEB_NIVEL_LOG': 'nivel_log',
        'SERVIDOR_WEB_ARQUIVO_LOG': 'arquivo_log',
        'SERVIDOR_WEB_CORS_HABILITADO': 'cors_habilitado',
        'SERVIDOR_WEB_TIPO_PROVEDOR': 'tipo_provedor',
        'SERVIDOR_WEB_ARQUIVO_JSON': 'caminho_arquivo_json',
    }
    
    # Configurações MySQL via ambiente
    mysql_env = {
        'MYSQL_HOST': 'host',
        'MYSQL_PORTA': 'porta',
        'MYSQL_USUARIO': 'usuario',
        'MYSQL_SENHA': 'senha',
        'MYSQL_BANCO': 'banco_dados',
        'MYSQL_SSL_HABILITADO': 'ssl_habilitado',
        'MYSQL_POOL_SIZE': 'pool_size',
    }
    
    for env_var, attr_name in mapeamento_env.items():
        valor = os.getenv(env_var)
        if valor is not None:
            # Converter tipos conforme necessário
            if attr_name in ['porta_preferencial']:
                valor = int(valor)
            elif attr_name in ['modo_debug', 'cors_habilitado']:
                valor = valor.lower() in ('true', '1', 'yes', 'on')
            
            setattr(config, attr_name, valor)
    
    # Configurar MySQL se necessário
    if config.tipo_provedor == "mysql":
        config_mysql = ConfiguracaoMySQL()
        
        for env_var, attr_name in mysql_env.items():
            valor = os.getenv(env_var)
            if valor is not None:
                # Converter tipos conforme necessário
                if attr_name in ['porta', 'pool_size']:
                    valor = int(valor)
                elif attr_name in ['ssl_habilitado']:
                    valor = valor.lower() in ('true', '1', 'yes', 'on')
                
                setattr(config_mysql, attr_name, valor)
        
        config.configuracao_mysql = config_mysql
    
    # Validar configuração carregada
    config.validar()
    
    return config


def criar_configuracao_exemplo(caminho: Union[str, Path]) -> None:
    """
    Cria um arquivo de configuração de exemplo.
    
    Args:
        caminho: Caminho onde criar o arquivo de exemplo
    """
    config = ConfiguracaoServidorWeb()
    config.salvar_arquivo(caminho)


def criar_configuracao_mysql_exemplo() -> ConfiguracaoMySQL:
    """
    Cria uma configuração MySQL de exemplo.
    
    Returns:
        ConfiguracaoMySQL com valores de exemplo
    """
    return ConfiguracaoMySQL(
        host="localhost",
        porta=3306,
        usuario="servidor_web_user",
        senha="senha_segura_aqui",
        banco_dados="servidor_web_integrado",
        ssl_habilitado=True,
        pool_size=10,
        max_overflow=20
    )


def criar_configuracao_completa_exemplo(caminho: Union[str, Path]) -> None:
    """
    Cria um arquivo de configuração completo de exemplo incluindo MySQL.
    
    Args:
        caminho: Caminho onde criar o arquivo de exemplo
    """
    config = ConfiguracaoServidorWeb()
    config.tipo_provedor = "mysql"
    config.configuracao_mysql = criar_configuracao_mysql_exemplo()
    config.salvar_arquivo(caminho)


def migrar_configuracao_para_mysql(
    config_atual: ConfiguracaoServidorWeb,
    config_mysql: ConfiguracaoMySQL
) -> ConfiguracaoServidorWeb:
    """
    Migra configuração existente para usar MySQL.
    
    Args:
        config_atual: Configuração atual (provavelmente JSON)
        config_mysql: Configuração MySQL a ser aplicada
        
    Returns:
        Nova configuração usando MySQL
    """
    # Criar nova configuração baseada na atual
    nova_config = ConfiguracaoServidorWeb(**config_atual.para_dict())
    
    # Alterar para MySQL
    nova_config.tipo_provedor = "mysql"
    nova_config.configuracao_mysql = config_mysql
    
    # Validar nova configuração
    nova_config.validar()
    
    return nova_config


def obter_configuracao_provedor_dados(config: ConfiguracaoServidorWeb) -> Dict[str, Any]:
    """
    Extrai configuração específica do provedor de dados.
    
    Args:
        config: Configuração completa do servidor web
        
    Returns:
        Dicionário com configuração do provedor de dados
    """
    if config.tipo_provedor == "mysql":
        if config.configuracao_mysql is None:
            raise ErroValidacaoConfiguracao("Configuração MySQL não encontrada")
        return {
            "tipo_provedor": "mysql",
            "mysql": config.configuracao_mysql.para_dict()
        }
    else:
        return {
            "tipo_provedor": "json",
            "json": {
                "caminho_arquivo": config.caminho_arquivo_json,
                "intervalo_observacao": config.intervalo_sincronizacao,
                "debounce_delay": config.debounce_delay
            }
        }


def validar_conexao_mysql(config_mysql: ConfiguracaoMySQL) -> bool:
    """
    Valida se é possível conectar ao MySQL com as configurações fornecidas.
    
    Args:
        config_mysql: Configuração MySQL a ser testada
        
    Returns:
        True se conexão for bem-sucedida, False caso contrário
    """
    try:
        # TODO: Implementar teste real de conexão quando MySQL for integrado
        # import mysql.connector
        # 
        # conexao = mysql.connector.connect(
        #     host=config_mysql.host,
        #     port=config_mysql.porta,
        #     user=config_mysql.usuario,
        #     password=config_mysql.senha,
        #     database=config_mysql.banco_dados,
        #     charset=config_mysql.charset,
        #     connect_timeout=config_mysql.timeout_conexao
        # )
        # conexao.close()
        
        # Por enquanto, apenas validar configuração
        config_mysql.validar()
        return True
        
    except Exception:
        return False