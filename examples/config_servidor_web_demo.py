#!/usr/bin/env python3
"""
Demonstração do sistema de configuração do servidor web integrado.

Este script mostra como usar o sistema de configuração flexível,
incluindo criação, validação, carregamento e diagnóstico de configurações.
"""

import json
import os
import tempfile
from pathlib import Path

# Importar módulos do sistema de configuração
from services.web_server import (
    ConfiguracaoServidorWeb,
    ConfigManager,
    obter_configuracao,
    diagnosticar_configuracao,
    gerar_relatorio_configuracao,
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao,
    verificar_porta_disponivel,
    encontrar_porta_disponivel
)


def demonstrar_configuracao_basica():
    """Demonstra uso básico da configuração."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Configuração Básica")
    print("=" * 60)
    
    # Criar configuração padrão
    config = ConfiguracaoServidorWeb()
    print(f"✅ Configuração padrão criada")
    print(f"   Porta: {config.porta_preferencial}")
    print(f"   Host: {config.host}")
    print(f"   Debug: {config.modo_debug}")
    print(f"   CORS: {config.cors_habilitado}")
    print()
    
    # Criar configuração personalizada
    config_custom = ConfiguracaoServidorWeb(
        porta_preferencial=8085,
        modo_debug=True,
        nivel_log="DEBUG",
        cors_origens=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    print(f"✅ Configuração personalizada criada")
    print(f"   Porta: {config_custom.porta_preferencial}")
    print(f"   Debug: {config_custom.modo_debug}")
    print(f"   Nível Log: {config_custom.nivel_log}")
    print(f"   CORS Origens: {config_custom.cors_origens}")
    print()


def demonstrar_validacao():
    """Demonstra validação de configurações."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Validação de Configurações")
    print("=" * 60)
    
    # Configuração válida
    try:
        config_valida = ConfiguracaoServidorWeb(
            porta_preferencial=8080,
            host="localhost",
            modo_debug=False
        )
        print("✅ Configuração válida criada com sucesso")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    # Configuração inválida - porta fora do intervalo
    try:
        config_invalida = ConfiguracaoServidorWeb(
            porta_preferencial=9000,  # Fora do intervalo padrão 8080-8090
            porta_minima=8080,
            porta_maxima=8090
        )
        print("❌ Configuração inválida foi aceita (não deveria)")
    except Exception as e:
        print(f"✅ Configuração inválida rejeitada corretamente: {type(e).__name__}")
    
    # Configuração inválida - host vazio
    try:
        config_host_vazio = ConfiguracaoServidorWeb(host="")
        print("❌ Host vazio foi aceito (não deveria)")
    except Exception as e:
        print(f"✅ Host vazio rejeitado corretamente: {type(e).__name__}")
    
    print()


def demonstrar_arquivo_json():
    """Demonstra salvamento e carregamento de arquivos JSON."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Arquivos JSON")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        arquivo_temp = f.name
    
    try:
        # Criar e salvar configuração
        config_original = ConfiguracaoServidorWeb(
            porta_preferencial=8085,
            modo_debug=True,
            nivel_log="DEBUG",
            cors_origens=["http://localhost:3000"]
        )
        
        config_original.salvar_arquivo(arquivo_temp)
        print(f"✅ Configuração salva em: {arquivo_temp}")
        
        # Carregar configuração
        config_carregada = ConfiguracaoServidorWeb.carregar_arquivo(arquivo_temp)
        print(f"✅ Configuração carregada do arquivo")
        print(f"   Porta: {config_carregada.porta_preferencial}")
        print(f"   Debug: {config_carregada.modo_debug}")
        print(f"   Nível Log: {config_carregada.nivel_log}")
        
        # Mostrar conteúdo do arquivo
        with open(arquivo_temp, 'r', encoding='utf-8') as f:
            conteudo = json.load(f)
        
        print(f"\n📄 Conteúdo do arquivo JSON (primeiras 5 chaves):")
        for i, (chave, valor) in enumerate(conteudo.items()):
            if i >= 5:
                print("   ...")
                break
            print(f"   {chave}: {valor}")
        
    finally:
        os.unlink(arquivo_temp)
        print(f"🗑️  Arquivo temporário removido")
    
    print()


def demonstrar_config_manager():
    """Demonstra uso do ConfigManager."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: ConfigManager")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        arquivo_temp = f.name
    
    try:
        # Criar manager
        manager = ConfigManager(
            caminho_config=arquivo_temp,
            monitorar_mudancas=False  # Desabilitar para demo
        )
        
        print(f"✅ ConfigManager criado")
        
        # Obter configuração inicial
        config = manager.obter_configuracao()
        print(f"   Porta inicial: {config.porta_preferencial}")
        
        # Atualizar configuração
        sucesso = manager.atualizar_configuracao(
            porta_preferencial=8085,
            modo_debug=True,
            nivel_log="DEBUG"
        )
        
        if sucesso:
            print(f"✅ Configuração atualizada com sucesso")
            config_atualizada = manager.obter_configuracao()
            print(f"   Nova porta: {config_atualizada.porta_preferencial}")
            print(f"   Debug: {config_atualizada.modo_debug}")
        else:
            print(f"❌ Falha ao atualizar configuração")
        
        # Informações do manager
        info = manager.obter_info_configuracao()
        print(f"\n📊 Informações do ConfigManager:")
        for chave, valor in info.items():
            print(f"   {chave}: {valor}")
        
    finally:
        os.unlink(arquivo_temp)
        print(f"🗑️  Arquivo temporário removido")
    
    print()


def demonstrar_diagnostico():
    """Demonstra diagnóstico de configurações."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Diagnóstico de Configurações")
    print("=" * 60)
    
    # Configuração para diagnóstico
    config = ConfiguracaoServidorWeb(
        porta_preferencial=8080,
        modo_debug=True,
        cors_origens=["*"],  # Pode gerar aviso de segurança
        permitir_directory_listing=True,  # Pode gerar aviso de segurança
        intervalo_sincronizacao=0.05  # Pode gerar aviso de performance
    )
    
    # Executar diagnóstico
    diagnostico = diagnosticar_configuracao(config)
    
    print(f"📋 Resultado do diagnóstico:")
    print(f"   Configuração válida: {diagnostico['configuracao_valida']}")
    print(f"   Erros: {len(diagnostico['erros'])}")
    print(f"   Avisos: {len(diagnostico['avisos'])}")
    print(f"   Informações: {len(diagnostico['informacoes'])}")
    
    if diagnostico['avisos']:
        print(f"\n⚠️  Avisos encontrados:")
        for aviso in diagnostico['avisos']:
            print(f"   - {aviso}")
    
    if diagnostico['informacoes']:
        print(f"\nℹ️  Informações:")
        for info in diagnostico['informacoes']:
            print(f"   - {info}")
    
    print()


def demonstrar_configuracoes_predefinidas():
    """Demonstra configurações predefinidas."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Configurações Predefinidas")
    print("=" * 60)
    
    # Configuração de desenvolvimento
    config_dev = criar_configuracao_desenvolvimento()
    print(f"🔧 Configuração de Desenvolvimento:")
    print(f"   Debug: {config_dev.modo_debug}")
    print(f"   Nível Log: {config_dev.nivel_log}")
    print(f"   Cache: {config_dev.cache_habilitado}")
    print(f"   Intervalo Sync: {config_dev.intervalo_sincronizacao}s")
    
    # Configuração de produção
    config_prod = criar_configuracao_producao()
    print(f"\n🚀 Configuração de Produção:")
    print(f"   Debug: {config_prod.modo_debug}")
    print(f"   Nível Log: {config_prod.nivel_log}")
    print(f"   Cache: {config_prod.cache_habilitado}")
    print(f"   Intervalo Sync: {config_prod.intervalo_sincronizacao}s")
    print(f"   Compressão: {config_prod.compressao_habilitada}")
    
    print()


def demonstrar_utilitarios_rede():
    """Demonstra utilitários de rede."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Utilitários de Rede")
    print("=" * 60)
    
    # Verificar porta específica
    porta_teste = 8080
    disponivel = verificar_porta_disponivel(porta_teste)
    print(f"🔍 Porta {porta_teste} disponível: {disponivel}")
    
    # Encontrar porta disponível
    porta_encontrada = encontrar_porta_disponivel(8080, 8090)
    if porta_encontrada:
        print(f"✅ Porta disponível encontrada: {porta_encontrada}")
    else:
        print(f"❌ Nenhuma porta disponível no intervalo 8080-8090")
    
    # Testar algumas portas altas (mais provável de estarem disponíveis)
    porta_alta = encontrar_porta_disponivel(60000, 60010)
    if porta_alta:
        print(f"✅ Porta alta disponível: {porta_alta}")
    
    print()


def demonstrar_relatorio_completo():
    """Demonstra geração de relatório completo."""
    print("=" * 60)
    print("DEMONSTRAÇÃO: Relatório Completo")
    print("=" * 60)
    
    # Criar configuração com alguns problemas para demonstrar
    config = ConfiguracaoServidorWeb(
        porta_preferencial=8080,
        modo_debug=False,
        cors_origens=["*"],  # Aviso de segurança
        permitir_directory_listing=True,  # Aviso de segurança
        max_tamanho_upload=200 * 1024 * 1024,  # Aviso de performance (200MB)
        diretorio_html="web_content_inexistente"  # Pode gerar erro
    )
    
    # Gerar relatório
    relatorio = gerar_relatorio_configuracao(config)
    print(relatorio)


def main():
    """Função principal da demonstração."""
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE CONFIGURAÇÃO DO SERVIDOR WEB")
    print("=" * 80)
    print()
    
    try:
        demonstrar_configuracao_basica()
        demonstrar_validacao()
        demonstrar_arquivo_json()
        demonstrar_config_manager()
        demonstrar_diagnostico()
        demonstrar_configuracoes_predefinidas()
        demonstrar_utilitarios_rede()
        demonstrar_relatorio_completo()
        
        print("🎉 Demonstração concluída com sucesso!")
        print("\n💡 Dicas:")
        print("   - Use ConfigManager para gerenciamento automático de configurações")
        print("   - Execute diagnósticos regulares para identificar problemas")
        print("   - Use configurações predefinidas como ponto de partida")
        print("   - Monitore portas disponíveis antes de iniciar o servidor")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()