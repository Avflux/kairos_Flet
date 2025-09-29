"""
Modelos de dados para o servidor web integrado.

Este módulo define as estruturas de dados utilizadas pelo sistema
de servidor web integrado, incluindo configurações, estado de
sincronização e dados do TopSidebarContainer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TipoProvedor(Enum):
    """Tipos de provedores de dados disponíveis."""
    JSON = "json"
    MYSQL = "mysql"


class StatusSincronizacao(Enum):
    """Status possíveis da sincronização de dados."""
    INATIVO = "inativo"
    ATIVO = "ativo"
    ERRO = "erro"
    PAUSADO = "pausado"


class BreakpointLayout(Enum):
    """Breakpoints para layout responsivo."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


@dataclass
class ConfiguracaoServidorWeb:
    """
    Configuração do servidor web integrado.
    
    Esta classe define todas as configurações possíveis para o
    servidor web integrado, incluindo parâmetros de rede, segurança
    e comportamento do sistema.
    """
    
    # Configurações básicas do servidor
    porta_preferencial: int = 8080
    portas_alternativas: List[int] = field(default_factory=lambda: [8081, 8082, 8083, 8084])
    host: str = "localhost"
    diretorio_html: str = "web_content"
    
    # Configurações de comportamento
    modo_debug: bool = False
    timeout_servidor: int = 30
    timeout_conexao: int = 10
    max_tentativas_porta: int = 5
    
    # Configurações de CORS
    cors_habilitado: bool = True
    cors_origens: List[str] = field(default_factory=lambda: ["*"])
    cors_metodos: List[str] = field(default_factory=lambda: ["GET", "POST", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    # Configurações de sincronização
    tipo_provedor: TipoProvedor = TipoProvedor.JSON
    arquivo_sincronizacao: str = "web_content/data/sync.json"
    intervalo_debounce: float = 0.5
    max_tentativas_sync: int = 3
    
    # Configurações de segurança
    validar_caminhos: bool = True
    permitir_directory_listing: bool = False
    max_tamanho_arquivo: int = 10 * 1024 * 1024  # 10MB
    
    # Configurações de performance
    cache_habilitado: bool = True
    cache_max_idade: int = 3600  # 1 hora
    compressao_habilitada: bool = True
    
    def validar(self) -> List[str]:
        """
        Valida as configurações e retorna lista de erros.
        
        Returns:
            Lista de mensagens de erro (vazia se válida)
        """
        erros = []
        
        # Validar porta
        if not (1024 <= self.porta_preferencial <= 65535):
            erros.append("Porta preferencial deve estar entre 1024 e 65535")
        
        # Validar portas alternativas
        for porta in self.portas_alternativas:
            if not (1024 <= porta <= 65535):
                erros.append(f"Porta alternativa {porta} deve estar entre 1024 e 65535")
        
        # Validar timeouts
        if self.timeout_servidor <= 0:
            erros.append("Timeout do servidor deve ser positivo")
        
        if self.timeout_conexao <= 0:
            erros.append("Timeout de conexão deve ser positivo")
        
        # Validar diretório HTML
        if not self.diretorio_html or not self.diretorio_html.strip():
            erros.append("Diretório HTML não pode estar vazio")
        
        # Validar arquivo de sincronização
        if not self.arquivo_sincronizacao or not self.arquivo_sincronizacao.strip():
            erros.append("Arquivo de sincronização não pode estar vazio")
        
        # Validar intervalo de debounce
        if self.intervalo_debounce < 0:
            erros.append("Intervalo de debounce deve ser não-negativo")
        
        return erros


@dataclass
class EstadoSincronizacao:
    """
    Estado atual da sincronização de dados.
    
    Esta classe mantém informações sobre o estado da sincronização
    entre a aplicação Flet e o WebView, incluindo timestamps,
    versões e informações de erro.
    """
    
    # Estado básico
    status: StatusSincronizacao = StatusSincronizacao.INATIVO
    ultima_atualizacao: Optional[datetime] = None
    proxima_tentativa: Optional[datetime] = None
    
    # Versionamento
    versao_atual: int = 0
    versao_webview: int = 0
    
    # Dados e estatísticas
    total_sincronizacoes: int = 0
    sincronizacoes_com_sucesso: int = 0
    sincronizacoes_com_erro: int = 0
    
    # Informações de erro
    ultimo_erro: Optional[str] = None
    codigo_ultimo_erro: Optional[str] = None
    tentativas_falha_consecutivas: int = 0
    
    # Performance
    tempo_ultima_sincronizacao_ms: Optional[float] = None
    tempo_medio_sincronizacao_ms: Optional[float] = None
    
    def registrar_sucesso(self, tempo_ms: float) -> None:
        """
        Registra uma sincronização bem-sucedida.
        
        Args:
            tempo_ms: Tempo da sincronização em milissegundos
        """
        self.status = StatusSincronizacao.ATIVO
        self.ultima_atualizacao = datetime.now()
        self.versao_atual += 1
        self.versao_webview = self.versao_atual
        
        self.total_sincronizacoes += 1
        self.sincronizacoes_com_sucesso += 1
        self.tentativas_falha_consecutivas = 0
        
        self.ultimo_erro = None
        self.codigo_ultimo_erro = None
        
        # Atualizar métricas de performance
        self.tempo_ultima_sincronizacao_ms = tempo_ms
        if self.tempo_medio_sincronizacao_ms is None:
            self.tempo_medio_sincronizacao_ms = tempo_ms
        else:
            # Média móvel simples
            self.tempo_medio_sincronizacao_ms = (
                self.tempo_medio_sincronizacao_ms * 0.8 + tempo_ms * 0.2
            )
    
    def registrar_erro(self, erro: str, codigo_erro: str = None) -> None:
        """
        Registra um erro de sincronização.
        
        Args:
            erro: Mensagem de erro
            codigo_erro: Código do erro (opcional)
        """
        self.status = StatusSincronizacao.ERRO
        self.ultima_atualizacao = datetime.now()
        
        self.total_sincronizacoes += 1
        self.sincronizacoes_com_erro += 1
        self.tentativas_falha_consecutivas += 1
        
        self.ultimo_erro = erro
        self.codigo_ultimo_erro = codigo_erro
    
    def calcular_taxa_sucesso(self) -> float:
        """
        Calcula a taxa de sucesso das sincronizações.
        
        Returns:
            Taxa de sucesso entre 0.0 e 1.0
        """
        if self.total_sincronizacoes == 0:
            return 0.0
        return self.sincronizacoes_com_sucesso / self.total_sincronizacoes


@dataclass
class DadosTimeTracker:
    """Dados do componente Time Tracker."""
    tempo_decorrido: int = 0  # em segundos
    esta_executando: bool = False
    esta_pausado: bool = False
    projeto_atual: str = ""
    tarefa_atual: str = ""
    tempo_total_hoje: int = 0
    meta_diaria: int = 8 * 3600  # 8 horas em segundos


@dataclass
class DadosFlowchart:
    """Dados do componente Flowchart."""
    progresso_workflow: float = 0.0  # 0.0 a 1.0
    estagio_atual: str = ""
    total_estagios: int = 0
    estagios_concluidos: int = 0
    workflow_ativo: str = ""
    tempo_estimado_restante: int = 0  # em minutos


@dataclass
class DadosNotificacoes:
    """Dados do centro de notificações."""
    total_notificacoes: int = 0
    notificacoes_nao_lidas: int = 0
    ultima_notificacao: Optional[str] = None
    timestamp_ultima: Optional[datetime] = None
    tipos_notificacao: List[str] = field(default_factory=list)


@dataclass
class DadosSidebar:
    """Dados do estado do sidebar."""
    sidebar_expandido: bool = False
    breakpoint_atual: BreakpointLayout = BreakpointLayout.DESKTOP
    largura_atual: int = 0
    altura_atual: int = 0
    componentes_visiveis: List[str] = field(default_factory=list)


@dataclass
class DadosTopSidebar:
    """
    Dados sincronizados do TopSidebarContainer.
    
    Esta classe agrega todos os dados dos componentes do TopSidebarContainer
    que devem ser sincronizados com o WebView.
    """
    
    # Timestamp da última atualização
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Dados dos componentes
    time_tracker: DadosTimeTracker = field(default_factory=DadosTimeTracker)
    flowchart: DadosFlowchart = field(default_factory=DadosFlowchart)
    notificacoes: DadosNotificacoes = field(default_factory=DadosNotificacoes)
    sidebar: DadosSidebar = field(default_factory=DadosSidebar)
    
    # Metadados
    versao: int = 1
    fonte: str = "TopSidebarContainer"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte os dados para dicionário para serialização JSON.
        
        Returns:
            Dicionário com todos os dados serializáveis
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "versao": self.versao,
            "fonte": self.fonte,
            "time_tracker": {
                "tempo_decorrido": self.time_tracker.tempo_decorrido,
                "esta_executando": self.time_tracker.esta_executando,
                "esta_pausado": self.time_tracker.esta_pausado,
                "projeto_atual": self.time_tracker.projeto_atual,
                "tarefa_atual": self.time_tracker.tarefa_atual,
                "tempo_total_hoje": self.time_tracker.tempo_total_hoje,
                "meta_diaria": self.time_tracker.meta_diaria
            },
            "flowchart": {
                "progresso_workflow": self.flowchart.progresso_workflow,
                "estagio_atual": self.flowchart.estagio_atual,
                "total_estagios": self.flowchart.total_estagios,
                "estagios_concluidos": self.flowchart.estagios_concluidos,
                "workflow_ativo": self.flowchart.workflow_ativo,
                "tempo_estimado_restante": self.flowchart.tempo_estimado_restante
            },
            "notificacoes": {
                "total_notificacoes": self.notificacoes.total_notificacoes,
                "notificacoes_nao_lidas": self.notificacoes.notificacoes_nao_lidas,
                "ultima_notificacao": self.notificacoes.ultima_notificacao,
                "timestamp_ultima": (
                    self.notificacoes.timestamp_ultima.isoformat()
                    if self.notificacoes.timestamp_ultima else None
                ),
                "tipos_notificacao": self.notificacoes.tipos_notificacao
            },
            "sidebar": {
                "sidebar_expandido": self.sidebar.sidebar_expandido,
                "breakpoint_atual": self.sidebar.breakpoint_atual.value,
                "largura_atual": self.sidebar.largura_atual,
                "altura_atual": self.sidebar.altura_atual,
                "componentes_visiveis": self.sidebar.componentes_visiveis
            }
        }
    
    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> 'DadosTopSidebar':
        """
        Cria instância a partir de dicionário.
        
        Args:
            dados: Dicionário com os dados
            
        Returns:
            Instância de DadosTopSidebar
        """
        instance = cls()
        
        # Metadados básicos
        if "timestamp" in dados:
            instance.timestamp = datetime.fromisoformat(dados["timestamp"])
        if "versao" in dados:
            instance.versao = dados["versao"]
        if "fonte" in dados:
            instance.fonte = dados["fonte"]
        
        # Time Tracker
        if "time_tracker" in dados:
            tt_data = dados["time_tracker"]
            instance.time_tracker = DadosTimeTracker(
                tempo_decorrido=tt_data.get("tempo_decorrido", 0),
                esta_executando=tt_data.get("esta_executando", False),
                esta_pausado=tt_data.get("esta_pausado", False),
                projeto_atual=tt_data.get("projeto_atual", ""),
                tarefa_atual=tt_data.get("tarefa_atual", ""),
                tempo_total_hoje=tt_data.get("tempo_total_hoje", 0),
                meta_diaria=tt_data.get("meta_diaria", 8 * 3600)
            )
        
        # Flowchart
        if "flowchart" in dados:
            fc_data = dados["flowchart"]
            instance.flowchart = DadosFlowchart(
                progresso_workflow=fc_data.get("progresso_workflow", 0.0),
                estagio_atual=fc_data.get("estagio_atual", ""),
                total_estagios=fc_data.get("total_estagios", 0),
                estagios_concluidos=fc_data.get("estagios_concluidos", 0),
                workflow_ativo=fc_data.get("workflow_ativo", ""),
                tempo_estimado_restante=fc_data.get("tempo_estimado_restante", 0)
            )
        
        # Notificações
        if "notificacoes" in dados:
            not_data = dados["notificacoes"]
            timestamp_ultima = None
            if not_data.get("timestamp_ultima"):
                timestamp_ultima = datetime.fromisoformat(not_data["timestamp_ultima"])
            
            instance.notificacoes = DadosNotificacoes(
                total_notificacoes=not_data.get("total_notificacoes", 0),
                notificacoes_nao_lidas=not_data.get("notificacoes_nao_lidas", 0),
                ultima_notificacao=not_data.get("ultima_notificacao"),
                timestamp_ultima=timestamp_ultima,
                tipos_notificacao=not_data.get("tipos_notificacao", [])
            )
        
        # Sidebar
        if "sidebar" in dados:
            sb_data = dados["sidebar"]
            breakpoint = BreakpointLayout.DESKTOP
            if "breakpoint_atual" in sb_data:
                try:
                    breakpoint = BreakpointLayout(sb_data["breakpoint_atual"])
                except ValueError:
                    pass
            
            instance.sidebar = DadosSidebar(
                sidebar_expandido=sb_data.get("sidebar_expandido", False),
                breakpoint_atual=breakpoint,
                largura_atual=sb_data.get("largura_atual", 0),
                altura_atual=sb_data.get("altura_atual", 0),
                componentes_visiveis=sb_data.get("componentes_visiveis", [])
            )
        
        return instance


@dataclass
class ConfiguracaoMySQL:
    """
    Configuração para conexão MySQL (futura implementação).
    
    Esta classe define as configurações necessárias para conectar
    com um banco de dados MySQL quando essa funcionalidade for
    implementada.
    """
    
    host: str = "localhost"
    porta: int = 3306
    usuario: str = ""
    senha: str = ""
    banco_dados: str = ""
    charset: str = "utf8mb4"
    
    # Configurações de pool de conexões
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # Configurações SSL
    ssl_habilitado: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    
    def obter_url_conexao(self, incluir_senha: bool = False) -> str:
        """
        Gera URL de conexão MySQL.
        
        Args:
            incluir_senha: Se deve incluir a senha na URL
            
        Returns:
            URL de conexão formatada
        """
        senha_parte = f":{self.senha}" if incluir_senha and self.senha else ""
        return f"mysql://{self.usuario}{senha_parte}@{self.host}:{self.porta}/{self.banco_dados}"