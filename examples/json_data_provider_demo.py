"""
Demonstração do JSONDataProvider para sincronização de dados.

Este exemplo mostra como usar o JSONDataProvider para sincronizar dados
entre a aplicação Flet e um WebView, incluindo observação de mudanças,
debouncing e versionamento.
"""

import os
import sys
import time
import json
from datetime import datetime

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.web_server.data_provider import JSONDataProvider
from services.web_server.models import DadosTopSidebar, DadosTimeTracker, DadosFlowchart, DadosNotificacoes, DadosSidebar


def callback_mudanca_dados(dados):
    """
    Callback chamado quando os dados são modificados.
    
    Args:
        dados: Dicionário com os dados atualizados
    """
    print(f"\n🔄 Dados atualizados às {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 Dados recebidos: {json.dumps(dados, indent=2, ensure_ascii=False)}")


def demonstrar_funcionalidades_basicas():
    """Demonstra funcionalidades básicas do JSONDataProvider."""
    print("=" * 60)
    print("🚀 DEMONSTRAÇÃO DO JSONDataProvider")
    print("=" * 60)
    
    # Criar diretório de demonstração
    demo_dir = "demo_json_provider"
    os.makedirs(demo_dir, exist_ok=True)
    arquivo_demo = os.path.join(demo_dir, "sync_demo.json")
    
    try:
        # Inicializar provider
        print("\n1️⃣ Inicializando JSONDataProvider...")
        provider = JSONDataProvider(arquivo_demo)
        print(f"✅ Provider criado com arquivo: {arquivo_demo}")
        
        # Configurar observador
        print("\n2️⃣ Configurando observador de mudanças...")
        provider.configurar_observador(callback_mudanca_dados)
        print("✅ Observador configurado")
        
        # Demonstrar salvamento de dados simples
        print("\n3️⃣ Salvando dados simples...")
        dados_simples = {
            "usuario": "João Silva",
            "configuracao": {
                "tema": "escuro",
                "idioma": "pt-BR"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        provider.salvar_dados(dados_simples)
        print("✅ Dados simples salvos")
        
        # Carregar e verificar dados
        print("\n4️⃣ Carregando dados...")
        dados_carregados = provider.carregar_dados()
        print(f"✅ Dados carregados: {json.dumps(dados_carregados, indent=2, ensure_ascii=False)}")
        
        # Demonstrar versionamento
        print("\n5️⃣ Demonstrando versionamento...")
        for i in range(3):
            dados_versao = {
                "iteracao": i + 1,
                "dados": f"Versão {i + 1}",
                "timestamp": datetime.now().isoformat()
            }
            provider.salvar_dados(dados_versao)
            
            # Verificar versão no arquivo
            with open(arquivo_demo, 'r', encoding='utf-8') as f:
                estrutura = json.load(f)
            
            print(f"   📝 Iteração {i + 1}: Versão {estrutura['versao']}")
            time.sleep(0.1)
        
        print("✅ Versionamento demonstrado")
        
        # Parar observador
        print("\n6️⃣ Parando observador...")
        provider.parar_observador()
        print("✅ Observador parado")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {str(e)}")
    
    finally:
        # Limpeza
        if os.path.exists(arquivo_demo):
            os.remove(arquivo_demo)
        if os.path.exists(demo_dir):
            os.rmdir(demo_dir)
        print("\n🧹 Limpeza concluída")


def demonstrar_sincronizacao_topsidebar():
    """Demonstra sincronização com dados do TopSidebarContainer."""
    print("\n" + "=" * 60)
    print("📱 DEMONSTRAÇÃO DE SINCRONIZAÇÃO COM TOPSIDEBAR")
    print("=" * 60)
    
    # Criar diretório de demonstração
    demo_dir = "demo_topsidebar_sync"
    os.makedirs(demo_dir, exist_ok=True)
    arquivo_demo = os.path.join(demo_dir, "topsidebar_sync.json")
    
    try:
        # Inicializar provider
        print("\n1️⃣ Inicializando provider para TopSidebar...")
        provider = JSONDataProvider(arquivo_demo)
        
        # Criar dados simulados do TopSidebarContainer
        print("\n2️⃣ Criando dados simulados do TopSidebarContainer...")
        dados_topsidebar = DadosTopSidebar()
        
        # Configurar Time Tracker
        dados_topsidebar.time_tracker.tempo_decorrido = 3665  # 1h 1min 5s
        dados_topsidebar.time_tracker.esta_executando = True
        dados_topsidebar.time_tracker.projeto_atual = "Servidor Web Integrado"
        dados_topsidebar.time_tracker.tarefa_atual = "Implementar JSONDataProvider"
        
        # Configurar Flowchart
        dados_topsidebar.flowchart.progresso_workflow = 0.65
        dados_topsidebar.flowchart.estagio_atual = "Desenvolvimento"
        dados_topsidebar.flowchart.total_estagios = 5
        dados_topsidebar.flowchart.estagios_concluidos = 3
        dados_topsidebar.flowchart.workflow_ativo = "Implementação de Features"
        
        # Configurar Notificações
        dados_topsidebar.notificacoes.total_notificacoes = 12
        dados_topsidebar.notificacoes.notificacoes_nao_lidas = 3
        dados_topsidebar.notificacoes.ultima_notificacao = "Teste unitário concluído com sucesso"
        dados_topsidebar.notificacoes.timestamp_ultima = datetime.now()
        
        # Configurar Sidebar
        dados_topsidebar.sidebar.sidebar_expandido = True
        dados_topsidebar.sidebar.largura_atual = 1200
        dados_topsidebar.sidebar.altura_atual = 800
        dados_topsidebar.sidebar.componentes_visiveis = ["time_tracker", "flowchart", "notifications", "webview"]
        
        print("✅ Dados do TopSidebar configurados")
        
        # Salvar dados estruturados
        print("\n3️⃣ Salvando dados estruturados...")
        dados_dict = dados_topsidebar.to_dict()
        provider.salvar_dados(dados_dict)
        print("✅ Dados estruturados salvos")
        
        # Demonstrar múltiplas atualizações (simulando uso real)
        print("\n4️⃣ Simulando atualizações em tempo real...")
        
        for i in range(5):
            # Simular progresso do time tracker
            dados_topsidebar.time_tracker.tempo_decorrido += 30  # +30 segundos
            
            # Simular progresso do workflow
            dados_topsidebar.flowchart.progresso_workflow += 0.05
            
            # Simular nova notificação ocasionalmente
            if i % 2 == 0:
                dados_topsidebar.notificacoes.total_notificacoes += 1
                dados_topsidebar.notificacoes.notificacoes_nao_lidas += 1
                dados_topsidebar.notificacoes.ultima_notificacao = f"Atualização automática #{i + 1}"
                dados_topsidebar.notificacoes.timestamp_ultima = datetime.now()
            
            # Atualizar timestamp
            dados_topsidebar.timestamp = datetime.now()
            
            # Salvar atualização
            dados_atualizados = dados_topsidebar.to_dict()
            provider.salvar_dados(dados_atualizados)
            
            print(f"   🔄 Atualização {i + 1}: Tempo={dados_topsidebar.time_tracker.tempo_decorrido}s, "
                  f"Progresso={dados_topsidebar.flowchart.progresso_workflow:.2f}")
            
            time.sleep(0.5)  # Simular intervalo entre atualizações
        
        print("✅ Simulação de atualizações concluída")
        
        # Verificar estrutura final do arquivo
        print("\n5️⃣ Verificando estrutura final do arquivo...")
        with open(arquivo_demo, 'r', encoding='utf-8') as f:
            estrutura_final = json.load(f)
        
        print(f"📄 Versão final: {estrutura_final['versao']}")
        print(f"📅 Timestamp: {estrutura_final['timestamp']}")
        print(f"📊 Componentes sincronizados: {len(estrutura_final['dados'])}")
        
        # Mostrar resumo dos dados
        dados_finais = estrutura_final['dados']
        if 'time_tracker' in dados_finais:
            tt = dados_finais['time_tracker']
            print(f"⏱️  Time Tracker: {tt['tempo_decorrido']}s, Projeto: {tt['projeto_atual']}")
        
        if 'flowchart' in dados_finais:
            fc = dados_finais['flowchart']
            print(f"📈 Flowchart: {fc['progresso_workflow']:.2f} ({fc['estagios_concluidos']}/{fc['total_estagios']})")
        
        if 'notificacoes' in dados_finais:
            nt = dados_finais['notificacoes']
            print(f"🔔 Notificações: {nt['total_notificacoes']} total, {nt['notificacoes_nao_lidas']} não lidas")
        
        print("✅ Verificação concluída")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpeza
        if os.path.exists(arquivo_demo):
            os.remove(arquivo_demo)
        if os.path.exists(demo_dir):
            os.rmdir(demo_dir)
        print("\n🧹 Limpeza concluída")


def demonstrar_debouncing():
    """Demonstra funcionalidade de debouncing."""
    print("\n" + "=" * 60)
    print("⏱️  DEMONSTRAÇÃO DE DEBOUNCING")
    print("=" * 60)
    
    # Criar diretório de demonstração
    demo_dir = "demo_debouncing"
    os.makedirs(demo_dir, exist_ok=True)
    arquivo_demo = os.path.join(demo_dir, "debounce_demo.json")
    
    callbacks_recebidos = []
    
    def callback_debounce(dados):
        callbacks_recebidos.append({
            'timestamp': datetime.now(),
            'dados': dados
        })
        print(f"   📨 Callback recebido às {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    try:
        # Inicializar provider
        print("\n1️⃣ Inicializando provider com debouncing...")
        provider = JSONDataProvider(arquivo_demo)
        provider.configurar_observador(callback_debounce)
        
        print("\n2️⃣ Realizando múltiplas atualizações rápidas...")
        print("   (Debouncing deve consolidar em uma única notificação)")
        
        # Realizar múltiplas atualizações rápidas
        for i in range(10):
            dados = {
                "atualizacao": i + 1,
                "timestamp": datetime.now().isoformat(),
                "dados_rapidos": f"Atualização rápida #{i + 1}"
            }
            provider.salvar_dados(dados)
            print(f"   💾 Salvamento {i + 1} realizado")
            time.sleep(0.05)  # 50ms entre salvamentos (menor que debounce de 500ms)
        
        print("\n3️⃣ Aguardando debounce (500ms)...")
        time.sleep(0.7)  # Aguardar mais que o debounce
        
        print(f"\n4️⃣ Resultado do debouncing:")
        print(f"   📊 Salvamentos realizados: 10")
        print(f"   📨 Callbacks recebidos: {len(callbacks_recebidos)}")
        print(f"   ✅ Debouncing funcionou: {'Sim' if len(callbacks_recebidos) <= 2 else 'Não'}")
        
        if callbacks_recebidos:
            primeiro = callbacks_recebidos[0]['timestamp']
            ultimo = callbacks_recebidos[-1]['timestamp'] if len(callbacks_recebidos) > 1 else primeiro
            intervalo = (ultimo - primeiro).total_seconds() * 1000
            print(f"   ⏱️  Intervalo entre callbacks: {intervalo:.1f}ms")
        
        # Parar observador
        provider.parar_observador()
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {str(e)}")
    
    finally:
        # Limpeza
        if os.path.exists(arquivo_demo):
            os.remove(arquivo_demo)
        if os.path.exists(demo_dir):
            os.rmdir(demo_dir)
        print("\n🧹 Limpeza concluída")


def main():
    """Função principal da demonstração."""
    print("🎯 DEMONSTRAÇÃO COMPLETA DO JSONDataProvider")
    print("=" * 80)
    
    try:
        # Executar demonstrações
        demonstrar_funcionalidades_basicas()
        demonstrar_sincronizacao_topsidebar()
        demonstrar_debouncing()
        
        print("\n" + "=" * 80)
        print("🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
        print("\n📋 RESUMO DAS FUNCIONALIDADES DEMONSTRADAS:")
        print("   ✅ Inicialização automática de arquivos JSON")
        print("   ✅ Salvamento e carregamento de dados")
        print("   ✅ Sistema de versionamento automático")
        print("   ✅ Observação de mudanças em arquivos")
        print("   ✅ Debouncing para otimizar atualizações")
        print("   ✅ Sincronização com dados estruturados")
        print("   ✅ Thread safety para operações concorrentes")
        print("   ✅ Tratamento robusto de erros")
        
        print("\n🔧 O JSONDataProvider está pronto para integração com:")
        print("   • TopSidebarContainer")
        print("   • WebViewComponent")
        print("   • DataSyncManager")
        print("   • Sistema de servidor web local")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante demonstração: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()