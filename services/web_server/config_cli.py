#!/usr/bin/env python3
"""
Interface de linha de comando para gerenciamento de configurações.

Este módulo fornece uma CLI para gerenciar configurações do servidor
web integrado, incluindo validação, diagnóstico e criação de arquivos.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .config import (
    ConfiguracaoServidorWeb,
    ErroConfiguracaoServidorWeb,
    criar_configuracao_exemplo
)
from .config_utils import (
    diagnosticar_configuracao,
    gerar_relatorio_configuracao,
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao,
    exportar_configuracao_para_env
)


def comando_validar(args) -> int:
    """
    Comando para validar um arquivo de configuração.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    try:
        config = ConfiguracaoServidorWeb.carregar_arquivo(args.arquivo)
        print(f"✅ Configuração válida: {args.arquivo}")
        
        if args.detalhado:
            diagnostico = diagnosticar_configuracao(config)
            
            if diagnostico['avisos']:
                print("\n⚠️  Avisos encontrados:")
                for aviso in diagnostico['avisos']:
                    print(f"   {aviso}")
            
            if diagnostico['informacoes']:
                print("\nℹ️  Informações:")
                for info in diagnostico['informacoes']:
                    print(f"   {info}")
        
        return 0
        
    except ErroConfiguracaoServidorWeb as e:
        print(f"❌ Erro de configuração: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1


def comando_diagnosticar(args) -> int:
    """
    Comando para diagnosticar uma configuração.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    try:
        config = ConfiguracaoServidorWeb.carregar_arquivo(args.arquivo)
        
        if args.formato == 'relatorio':
            relatorio = gerar_relatorio_configuracao(config)
            print(relatorio)
        else:
            diagnostico = diagnosticar_configuracao(config)
            print(json.dumps(diagnostico, indent=2, ensure_ascii=False))
        
        return 0 if diagnostico['configuracao_valida'] else 1
        
    except Exception as e:
        print(f"❌ Erro ao diagnosticar: {e}")
        return 1


def comando_criar(args) -> int:
    """
    Comando para criar arquivo de configuração.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    try:
        if args.tipo == 'padrao':
            config = ConfiguracaoServidorWeb()
        elif args.tipo == 'desenvolvimento':
            config = criar_configuracao_desenvolvimento()
        elif args.tipo == 'producao':
            config = criar_configuracao_producao()
        else:
            print(f"❌ Tipo de configuração inválido: {args.tipo}")
            return 1
        
        # Verificar se arquivo já existe
        if Path(args.arquivo).exists() and not args.sobrescrever:
            print(f"❌ Arquivo já existe: {args.arquivo}")
            print("   Use --sobrescrever para substituir")
            return 1
        
        config.salvar_arquivo(args.arquivo)
        print(f"✅ Configuração criada: {args.arquivo}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return 1


def comando_exportar_env(args) -> int:
    """
    Comando para exportar configuração como variáveis de ambiente.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    try:
        config = ConfiguracaoServidorWeb.carregar_arquivo(args.arquivo)
        env_vars = exportar_configuracao_para_env(config)
        
        if args.saida:
            with open(args.saida, 'w', encoding='utf-8') as f:
                f.write(env_vars)
            print(f"✅ Variáveis de ambiente exportadas para: {args.saida}")
        else:
            print(env_vars)
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
        return 1


def comando_mostrar(args) -> int:
    """
    Comando para mostrar configuração atual.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        Código de saída (0 = sucesso, 1 = erro)
    """
    try:
        config = ConfiguracaoServidorWeb.carregar_arquivo(args.arquivo)
        
        if args.formato == 'json':
            print(json.dumps(config.para_dict(), indent=2, ensure_ascii=False))
        else:
            # Formato legível
            print("CONFIGURAÇÃO DO SERVIDOR WEB")
            print("=" * 40)
            
            dados = config.para_dict()
            for chave, valor in dados.items():
                if isinstance(valor, list):
                    valor_str = ', '.join(str(v) for v in valor)
                else:
                    valor_str = str(valor)
                
                print(f"{chave}: {valor_str}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao mostrar configuração: {e}")
        return 1


def criar_parser() -> argparse.ArgumentParser:
    """
    Cria o parser de argumentos da linha de comando.
    
    Returns:
        ArgumentParser configurado
    """
    parser = argparse.ArgumentParser(
        description="Gerenciador de configurações do servidor web integrado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Validar configuração
  python -m services.web_server.config_cli validar config.json

  # Criar configuração padrão
  python -m services.web_server.config_cli criar --tipo padrao config.json

  # Diagnosticar configuração
  python -m services.web_server.config_cli diagnosticar config.json

  # Exportar como variáveis de ambiente
  python -m services.web_server.config_cli exportar-env config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Comando validar
    parser_validar = subparsers.add_parser(
        'validar',
        help='Valida um arquivo de configuração'
    )
    parser_validar.add_argument(
        'arquivo',
        help='Caminho do arquivo de configuração'
    )
    parser_validar.add_argument(
        '--detalhado',
        action='store_true',
        help='Mostra informações detalhadas'
    )
    parser_validar.set_defaults(func=comando_validar)
    
    # Comando diagnosticar
    parser_diagnosticar = subparsers.add_parser(
        'diagnosticar',
        help='Executa diagnóstico completo da configuração'
    )
    parser_diagnosticar.add_argument(
        'arquivo',
        help='Caminho do arquivo de configuração'
    )
    parser_diagnosticar.add_argument(
        '--formato',
        choices=['json', 'relatorio'],
        default='relatorio',
        help='Formato de saída'
    )
    parser_diagnosticar.set_defaults(func=comando_diagnosticar)
    
    # Comando criar
    parser_criar = subparsers.add_parser(
        'criar',
        help='Cria um novo arquivo de configuração'
    )
    parser_criar.add_argument(
        'arquivo',
        help='Caminho do arquivo a ser criado'
    )
    parser_criar.add_argument(
        '--tipo',
        choices=['padrao', 'desenvolvimento', 'producao'],
        default='padrao',
        help='Tipo de configuração'
    )
    parser_criar.add_argument(
        '--sobrescrever',
        action='store_true',
        help='Sobrescrever arquivo existente'
    )
    parser_criar.set_defaults(func=comando_criar)
    
    # Comando exportar-env
    parser_exportar = subparsers.add_parser(
        'exportar-env',
        help='Exporta configuração como variáveis de ambiente'
    )
    parser_exportar.add_argument(
        'arquivo',
        help='Caminho do arquivo de configuração'
    )
    parser_exportar.add_argument(
        '--saida',
        help='Arquivo de saída (padrão: stdout)'
    )
    parser_exportar.set_defaults(func=comando_exportar_env)
    
    # Comando mostrar
    parser_mostrar = subparsers.add_parser(
        'mostrar',
        help='Mostra configuração atual'
    )
    parser_mostrar.add_argument(
        'arquivo',
        help='Caminho do arquivo de configuração'
    )
    parser_mostrar.add_argument(
        '--formato',
        choices=['json', 'legivel'],
        default='legivel',
        help='Formato de saída'
    )
    parser_mostrar.set_defaults(func=comando_mostrar)
    
    return parser


def main():
    """Função principal da CLI."""
    parser = criar_parser()
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())