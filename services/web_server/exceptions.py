"""
Exceções personalizadas para o servidor web integrado.

Este módulo define a hierarquia de exceções específicas para o sistema
de servidor web integrado, com mensagens em português brasileiro.
"""


class ServidorWebIntegradoError(Exception):
    """
    Exceção base para erros do servidor web integrado.
    
    Esta é a classe base para todas as exceções específicas do sistema
    de servidor web integrado. Todas as outras exceções do módulo
    devem herdar desta classe.
    """
    
    def __init__(self, mensagem: str, codigo_erro: str = None):
        """
        Inicializa a exceção.
        
        Args:
            mensagem: Mensagem de erro em português
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo_erro = codigo_erro
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        if self.codigo_erro:
            return f"[{self.codigo_erro}] {self.mensagem}"
        return self.mensagem


class ServidorWebError(ServidorWebIntegradoError):
    """
    Erro relacionado ao servidor web HTTP.
    
    Esta exceção é levantada quando há problemas com o servidor web local,
    como falha na inicialização, porta ocupada, ou problemas de rede.
    """
    
    def __init__(self, mensagem: str, porta: int = None, codigo_erro: str = None):
        """
        Inicializa a exceção do servidor web.
        
        Args:
            mensagem: Mensagem de erro em português
            porta: Porta onde ocorreu o erro (opcional)
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem, codigo_erro)
        self.porta = porta
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        base_msg = super().__str__()
        if self.porta:
            return f"{base_msg} (Porta: {self.porta})"
        return base_msg


class WebViewError(ServidorWebIntegradoError):
    """
    Erro relacionado ao componente WebView.
    
    Esta exceção é levantada quando há problemas com o WebView do Flet,
    como falha no carregamento, erro de JavaScript, ou problemas de renderização.
    """
    
    def __init__(self, mensagem: str, url: str = None, codigo_erro: str = None):
        """
        Inicializa a exceção do WebView.
        
        Args:
            mensagem: Mensagem de erro em português
            url: URL onde ocorreu o erro (opcional)
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem, codigo_erro)
        self.url = url
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        base_msg = super().__str__()
        if self.url:
            return f"{base_msg} (URL: {self.url})"
        return base_msg


class SincronizacaoError(ServidorWebIntegradoError):
    """
    Erro relacionado à sincronização de dados.
    
    Esta exceção é levantada quando há problemas na sincronização de dados
    entre a aplicação Flet e o WebView, incluindo erros de I/O, formato
    de dados inválido, ou falhas de comunicação.
    """
    
    def __init__(self, mensagem: str, arquivo: str = None, codigo_erro: str = None):
        """
        Inicializa a exceção de sincronização.
        
        Args:
            mensagem: Mensagem de erro em português
            arquivo: Arquivo onde ocorreu o erro (opcional)
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem, codigo_erro)
        self.arquivo = arquivo
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        base_msg = super().__str__()
        if self.arquivo:
            return f"{base_msg} (Arquivo: {self.arquivo})"
        return base_msg


class ConfiguracaoError(ServidorWebIntegradoError):
    """
    Erro relacionado à configuração do sistema.
    
    Esta exceção é levantada quando há problemas com as configurações
    do servidor web integrado, como valores inválidos, arquivos de
    configuração corrompidos, ou parâmetros obrigatórios ausentes.
    """
    
    def __init__(self, mensagem: str, parametro: str = None, codigo_erro: str = None):
        """
        Inicializa a exceção de configuração.
        
        Args:
            mensagem: Mensagem de erro em português
            parametro: Parâmetro de configuração problemático (opcional)
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem, codigo_erro)
        self.parametro = parametro
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        base_msg = super().__str__()
        if self.parametro:
            return f"{base_msg} (Parâmetro: {self.parametro})"
        return base_msg


class RecursoIndisponivelError(ServidorWebIntegradoError):
    """
    Erro quando um recurso necessário não está disponível.
    
    Esta exceção é levantada quando recursos necessários para o
    funcionamento do sistema não estão disponíveis, como portas de rede,
    arquivos de sistema, ou dependências externas.
    """
    
    def __init__(self, mensagem: str, recurso: str = None, codigo_erro: str = None):
        """
        Inicializa a exceção de recurso indisponível.
        
        Args:
            mensagem: Mensagem de erro em português
            recurso: Nome do recurso indisponível (opcional)
            codigo_erro: Código opcional para identificação do erro
        """
        super().__init__(mensagem, codigo_erro)
        self.recurso = recurso
    
    def __str__(self) -> str:
        """Retorna a representação string da exceção."""
        base_msg = super().__str__()
        if self.recurso:
            return f"{base_msg} (Recurso: {self.recurso})"
        return base_msg


# Códigos de erro padronizados
class CodigosErro:
    """Códigos de erro padronizados para facilitar o tratamento."""
    
    # Erros do servidor web
    SERVIDOR_PORTA_OCUPADA = "SRV001"
    SERVIDOR_FALHA_INICIALIZACAO = "SRV002"
    SERVIDOR_FALHA_PARADA = "SRV003"
    SERVIDOR_NAO_RESPONSIVO = "SRV004"
    
    # Erros do WebView
    WEBVIEW_FALHA_CARREGAMENTO = "WV001"
    WEBVIEW_ERRO_JAVASCRIPT = "WV002"
    WEBVIEW_URL_INVALIDA = "WV003"
    WEBVIEW_TIMEOUT = "WV004"
    
    # Erros de sincronização
    SYNC_ARQUIVO_NAO_ENCONTRADO = "SYNC001"
    SYNC_FORMATO_INVALIDO = "SYNC002"
    SYNC_PERMISSAO_NEGADA = "SYNC003"
    SYNC_TIMEOUT = "SYNC004"
    SYNC_DADOS_CORROMPIDOS = "SYNC005"
    
    # Erros de configuração
    CONFIG_PARAMETRO_OBRIGATORIO = "CFG001"
    CONFIG_VALOR_INVALIDO = "CFG002"
    CONFIG_ARQUIVO_CORROMPIDO = "CFG003"
    CONFIG_PERMISSAO_NEGADA = "CFG004"
    
    # Erros de recursos
    RECURSO_PORTA_INDISPONIVEL = "REC001"
    RECURSO_ARQUIVO_BLOQUEADO = "REC002"
    RECURSO_MEMORIA_INSUFICIENTE = "REC003"
    RECURSO_DEPENDENCIA_AUSENTE = "REC004"