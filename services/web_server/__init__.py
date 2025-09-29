"""
Servidor Web Integrado para TopSidebarContainer.

Este pacote fornece funcionalidades para integrar um servidor web
simples ao TopSidebarContainer, permitindo hospedar conteúdo HTML
e sincronizar dados em tempo real.

Módulos principais:
- config: Configuração do servidor web
- config_manager: Gerenciamento de configurações
- config_utils: Utilitários de configuração
- config_cli: Interface de linha de comando
"""

from .config import (
    ConfiguracaoServidorWeb,
    ErroConfiguracaoServidorWeb,
    ErroValidacaoConfiguracao,
    ErroCarregamentoConfiguracao,
    NivelLog,
    obter_configuracao_padrao,
    carregar_configuracao_do_ambiente,
    criar_configuracao_exemplo
)

from .config_manager import (
    ConfigManager,
    obter_config_manager,
    obter_configuracao,
    recarregar_configuracao,
    atualizar_configuracao
)

from .config_utils import (
    verificar_porta_disponivel,
    encontrar_porta_disponivel,
    validar_diretorio_html,
    validar_arquivo_index,
    diagnosticar_configuracao,
    gerar_relatorio_configuracao,
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao,
    exportar_configuracao_para_env
)

__version__ = "1.0.0"
__author__ = "Servidor Web Integrado Team"

__all__ = [
    # Classes principais
    'ConfiguracaoServidorWeb',
    'ConfigManager',
    'NivelLog',
    
    # Exceções
    'ErroConfiguracaoServidorWeb',
    'ErroValidacaoConfiguracao', 
    'ErroCarregamentoConfiguracao',
    
    # Funções de configuração
    'obter_configuracao_padrao',
    'carregar_configuracao_do_ambiente',
    'criar_configuracao_exemplo',
    
    # Funções do gerenciador
    'obter_config_manager',
    'obter_configuracao',
    'recarregar_configuracao',
    'atualizar_configuracao',
    
    # Utilitários
    'verificar_porta_disponivel',
    'encontrar_porta_disponivel',
    'validar_diretorio_html',
    'validar_arquivo_index',
    'diagnosticar_configuracao',
    'gerar_relatorio_configuracao',
    'criar_configuracao_desenvolvimento',
    'criar_configuracao_producao',
    'exportar_configuracao_para_env',
]