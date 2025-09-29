"""
Utilitários para configuração do servidor web integrado.

Este módulo fornece funções utilitárias para validação,
debug e manipulação de configurações do servidor web.
"""

import json
import logging
import os
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from .config import ConfiguracaoServidorWeb, ErroValidacaoConfiguracao


def verificar_porta_disponivel(porta: int, host: str = "localhost") -> bool:
    """
    Verifica se uma porta está disponível para uso.
    
    Args:
        porta: Número da porta para verificar
        host: Host para verificar (padrão: localhost)
        
    Returns:
        True se a porta estiver disponível
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            resultado = sock.connect_ex((host, porta))
            return resultado != 0
    except Exception:
        return False


def encontrar_porta_disponivel(
    porta_inicial: int = 8080,
    porta_final: int = 8090,
    host: str = "localhost"
) -> Optional[int]:
    """
    Encontra a primeira porta disponível em um intervalo.
    
    Args:
        porta_inicial: Porta inicial do intervalo
        porta_final: Porta final do intervalo
        host: Host para verificar
        
    Returns:
        Primeira porta disponível ou None se nenhuma estiver disponível
    """
    for porta in range(porta_inicial, porta_final + 1):
        if verificar_porta_disponivel(porta, host):
            return porta
    return None


def validar_diretorio_html(caminho: str) -> Tuple[bool, List[str]]:
    """
    Valida se um diretório HTML é válido e acessível.
    
    Args:
        caminho: Caminho do diretório para validar
        
    Returns:
        Tupla (é_válido, lista_de_erros)
    """
    erros = []
    caminho_path = Path(caminho)
    
    # Verificar se o diretório existe
    if not caminho_path.exists():
        erros.append(f"Diretório não existe: {caminho}")
        return False, erros
    
    # Verificar se é um diretório
    if not caminho_path.is_dir():
        erros.append(f"Caminho não é um diretório: {caminho}")
        return False, erros
    
    # Verificar permissões de leitura
    if not os.access(caminho_path, os.R_OK):
        erros.append(f"Sem permissão de leitura no diretório: {caminho}")
    
    # Verificar se contém arquivos HTML
    arquivos_html = list(caminho_path.glob("*.html"))
    if not arquivos_html:
        erros.append(f"Nenhum arquivo HTML encontrado no diretório: {caminho}")
    
    return len(erros) == 0, erros


def validar_arquivo_index(diretorio_html: str, arquivo_index: str) -> Tuple[bool, List[str]]:
    """
    Valida se o arquivo index existe e é acessível.
    
    Args:
        diretorio_html: Diretório HTML base
        arquivo_index: Nome do arquivo index
        
    Returns:
        Tupla (é_válido, lista_de_erros)
    """
    erros = []
    caminho_index = Path(diretorio_html) / arquivo_index
    
    # Verificar se o arquivo existe
    if not caminho_index.exists():
        erros.append(f"Arquivo index não existe: {caminho_index}")
        return False, erros
    
    # Verificar se é um arquivo
    if not caminho_index.is_file():
        erros.append(f"Index não é um arquivo: {caminho_index}")
        return False, erros
    
    # Verificar permissões de leitura
    if not os.access(caminho_index, os.R_OK):
        erros.append(f"Sem permissão de leitura no arquivo index: {caminho_index}")
    
    # Verificar se é um arquivo HTML válido (básico)
    try:
        with open(caminho_index, 'r', encoding='utf-8') as f:
            conteudo = f.read(1024)  # Ler apenas os primeiros 1024 caracteres
            if not any(tag in conteudo.lower() for tag in ['<html', '<head', '<body']):
                erros.append(f"Arquivo index não parece ser HTML válido: {caminho_index}")
    except Exception as e:
        erros.append(f"Erro ao ler arquivo index: {e}")
    
    return len(erros) == 0, erros


def validar_cors_origens(origens: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida configurações de CORS origens.
    
    Args:
        origens: Lista de origens CORS
        
    Returns:
        Tupla (é_válido, lista_de_erros)
    """
    erros = []
    
    for origem in origens:
        if origem == "*":
            continue  # Wildcard é válido
        
        try:
            parsed = urlparse(origem)
            if not parsed.scheme or not parsed.netloc:
                erros.append(f"Origem CORS inválida: {origem}")
        except Exception:
            erros.append(f"Erro ao analisar origem CORS: {origem}")
    
    return len(erros) == 0, erros


def diagnosticar_configuracao(config: ConfiguracaoServidorWeb) -> Dict[str, Any]:
    """
    Executa diagnóstico completo de uma configuração.
    
    Args:
        config: Configuração para diagnosticar
        
    Returns:
        Dicionário com resultados do diagnóstico
    """
    diagnostico = {
        'configuracao_valida': True,
        'erros': [],
        'avisos': [],
        'informacoes': [],
        'detalhes': {}
    }
    
    try:
        # Validar configuração básica
        config.validar()
        diagnostico['informacoes'].append("Configuração básica válida")
    except ErroValidacaoConfiguracao as e:
        diagnostico['configuracao_valida'] = False
        diagnostico['erros'].append(f"Erro de validação: {e}")
    
    # Verificar porta disponível
    porta_disponivel = verificar_porta_disponivel(config.porta_preferencial, config.host)
    diagnostico['detalhes']['porta_disponivel'] = porta_disponivel
    
    if not porta_disponivel:
        diagnostico['avisos'].append(
            f"Porta preferencial {config.porta_preferencial} não está disponível"
        )
        
        # Tentar encontrar porta alternativa
        porta_alternativa = encontrar_porta_disponivel(
            config.porta_minima, config.porta_maxima, config.host
        )
        if porta_alternativa:
            diagnostico['informacoes'].append(
                f"Porta alternativa disponível: {porta_alternativa}"
            )
        else:
            diagnostico['erros'].append(
                f"Nenhuma porta disponível no intervalo {config.porta_minima}-{config.porta_maxima}"
            )
    
    # Validar diretório HTML
    dir_valido, erros_dir = validar_diretorio_html(config.diretorio_html)
    diagnostico['detalhes']['diretorio_html_valido'] = dir_valido
    
    if not dir_valido:
        diagnostico['erros'].extend(erros_dir)
    else:
        diagnostico['informacoes'].append("Diretório HTML válido")
        
        # Validar arquivo index
        index_valido, erros_index = validar_arquivo_index(
            config.diretorio_html, config.arquivo_index
        )
        diagnostico['detalhes']['arquivo_index_valido'] = index_valido
        
        if not index_valido:
            diagnostico['erros'].extend(erros_index)
        else:
            diagnostico['informacoes'].append("Arquivo index válido")
    
    # Validar CORS
    if config.cors_habilitado:
        cors_valido, erros_cors = validar_cors_origens(config.cors_origens)
        diagnostico['detalhes']['cors_valido'] = cors_valido
        
        if not cors_valido:
            diagnostico['erros'].extend(erros_cors)
        else:
            diagnostico['informacoes'].append("Configuração CORS válida")
    
    # Verificar configurações de segurança
    if not config.validar_caminhos:
        diagnostico['avisos'].append(
            "Validação de caminhos desabilitada - pode ser um risco de segurança"
        )
    
    if config.permitir_directory_listing:
        diagnostico['avisos'].append(
            "Directory listing habilitado - pode expor estrutura de arquivos"
        )
    
    if "*" in config.cors_origens and config.cors_habilitado:
        diagnostico['avisos'].append(
            "CORS configurado para aceitar qualquer origem - pode ser um risco de segurança"
        )
    
    # Verificar configurações de performance
    if config.intervalo_sincronizacao < 0.1:
        diagnostico['avisos'].append(
            "Intervalo de sincronização muito baixo - pode impactar performance"
        )
    
    if config.max_tamanho_upload > 100 * 1024 * 1024:  # 100MB
        diagnostico['avisos'].append(
            "Tamanho máximo de upload muito alto - pode impactar performance"
        )
    
    # Atualizar status geral
    if diagnostico['erros']:
        diagnostico['configuracao_valida'] = False
    
    return diagnostico


def gerar_relatorio_configuracao(config: ConfiguracaoServidorWeb) -> str:
    """
    Gera um relatório detalhado da configuração.
    
    Args:
        config: Configuração para gerar relatório
        
    Returns:
        String com relatório formatado
    """
    diagnostico = diagnosticar_configuracao(config)
    
    relatorio = []
    relatorio.append("=" * 60)
    relatorio.append("RELATÓRIO DE CONFIGURAÇÃO DO SERVIDOR WEB")
    relatorio.append("=" * 60)
    relatorio.append("")
    
    # Status geral
    status = "VÁLIDA" if diagnostico['configuracao_valida'] else "INVÁLIDA"
    relatorio.append(f"Status Geral: {status}")
    relatorio.append("")
    
    # Configurações principais
    relatorio.append("CONFIGURAÇÕES PRINCIPAIS:")
    relatorio.append(f"  Porta Preferencial: {config.porta_preferencial}")
    relatorio.append(f"  Host: {config.host}")
    relatorio.append(f"  Diretório HTML: {config.diretorio_html}")
    relatorio.append(f"  Arquivo Index: {config.arquivo_index}")
    relatorio.append(f"  Modo Debug: {config.modo_debug}")
    relatorio.append(f"  Nível de Log: {config.nivel_log}")
    relatorio.append("")
    
    # Configurações de segurança
    relatorio.append("CONFIGURAÇÕES DE SEGURANÇA:")
    relatorio.append(f"  CORS Habilitado: {config.cors_habilitado}")
    relatorio.append(f"  CORS Origens: {', '.join(config.cors_origens)}")
    relatorio.append(f"  Validar Caminhos: {config.validar_caminhos}")
    relatorio.append(f"  Directory Listing: {config.permitir_directory_listing}")
    relatorio.append(f"  Max Upload: {config.max_tamanho_upload / 1024 / 1024:.1f}MB")
    relatorio.append("")
    
    # Erros
    if diagnostico['erros']:
        relatorio.append("ERROS ENCONTRADOS:")
        for erro in diagnostico['erros']:
            relatorio.append(f"  ❌ {erro}")
        relatorio.append("")
    
    # Avisos
    if diagnostico['avisos']:
        relatorio.append("AVISOS:")
        for aviso in diagnostico['avisos']:
            relatorio.append(f"  ⚠️  {aviso}")
        relatorio.append("")
    
    # Informações
    if diagnostico['informacoes']:
        relatorio.append("INFORMAÇÕES:")
        for info in diagnostico['informacoes']:
            relatorio.append(f"  ℹ️  {info}")
        relatorio.append("")
    
    relatorio.append("=" * 60)
    
    return "\n".join(relatorio)


def criar_configuracao_desenvolvimento() -> ConfiguracaoServidorWeb:
    """
    Cria uma configuração otimizada para desenvolvimento.
    
    Returns:
        ConfiguracaoServidorWeb configurada para desenvolvimento
    """
    return ConfiguracaoServidorWeb(
        modo_debug=True,
        nivel_log="DEBUG",
        cors_habilitado=True,
        cors_origens=["*"],
        validar_caminhos=True,
        permitir_directory_listing=False,
        intervalo_sincronizacao=0.5,
        debounce_delay=0.2,
        cache_habilitado=False,  # Desabilitar cache em desenvolvimento
    )


def criar_configuracao_producao() -> ConfiguracaoServidorWeb:
    """
    Cria uma configuração otimizada para produção.
    
    Returns:
        ConfiguracaoServidorWeb configurada para produção
    """
    return ConfiguracaoServidorWeb(
        modo_debug=False,
        nivel_log="WARNING",
        cors_habilitado=True,
        cors_origens=["http://localhost:*"],  # Mais restritivo
        validar_caminhos=True,
        permitir_directory_listing=False,
        intervalo_sincronizacao=2.0,
        debounce_delay=1.0,
        cache_habilitado=True,
        cache_max_age=3600,
        compressao_habilitada=True,
    )


def exportar_configuracao_para_env(config: ConfiguracaoServidorWeb) -> str:
    """
    Exporta configuração como variáveis de ambiente.
    
    Args:
        config: Configuração para exportar
        
    Returns:
        String com variáveis de ambiente
    """
    env_vars = []
    
    # Mapear configurações para variáveis de ambiente
    mapeamento = {
        'porta_preferencial': 'SERVIDOR_WEB_PORTA',
        'host': 'SERVIDOR_WEB_HOST',
        'modo_debug': 'SERVIDOR_WEB_DEBUG',
        'diretorio_html': 'SERVIDOR_WEB_DIRETORIO_HTML',
        'nivel_log': 'SERVIDOR_WEB_NIVEL_LOG',
        'arquivo_log': 'SERVIDOR_WEB_ARQUIVO_LOG',
        'cors_habilitado': 'SERVIDOR_WEB_CORS_HABILITADO',
    }
    
    for attr, env_var in mapeamento.items():
        valor = getattr(config, attr)
        if valor is not None:
            if isinstance(valor, bool):
                valor = 'true' if valor else 'false'
            env_vars.append(f"export {env_var}={valor}")
    
    return "\n".join(env_vars)