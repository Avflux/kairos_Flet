"""
Demonstração do WebServerManager.

Este exemplo mostra como usar o WebServerManager para inicializar
um servidor web local e servir arquivos HTML.
"""

import sys
import time
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.web_server.server_manager import WebServerManager
from services.web_server.models import ConfiguracaoServidorWeb


def criar_conteudo_demo():
    """Cria conteúdo HTML de demonstração."""
    # Criar diretório de conteúdo web
    web_dir = Path("web_content_demo")
    web_dir.mkdir(exist_ok=True)
    
    # Página principal
    (web_dir / "index.html").write_text("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Demo WebServerManager</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .status {
                background: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #4caf50;
            }
            .info {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }
            button {
                background: #4caf50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Demo WebServerManager</h1>
            
            <div class="status">
                <strong>✅ Servidor Web Ativo!</strong><br>
                O WebServerManager está funcionando corretamente e servindo este conteúdo HTML.
            </div>
            
            <div class="info">
                <h3>📋 Funcionalidades Demonstradas:</h3>
                <ul>
                    <li>✅ Descoberta automática de portas disponíveis</li>
                    <li>✅ Servir arquivos HTML estáticos</li>
                    <li>✅ Inicialização e parada graceful do servidor</li>
                    <li>✅ Tratamento de erros robusto</li>
                    <li>✅ Configuração flexível</li>
                    <li>✅ Headers CORS configuráveis</li>
                    <li>✅ Logs em português</li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🔧 Configurações Utilizadas:</h3>
                <ul>
                    <li><strong>Porta Preferencial:</strong> 8080</li>
                    <li><strong>Portas Alternativas:</strong> 8081, 8082, 8083</li>
                    <li><strong>Diretório HTML:</strong> web_content_demo</li>
                    <li><strong>CORS:</strong> Habilitado</li>
                    <li><strong>Modo Debug:</strong> Ativo</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button onclick="window.location.reload()">🔄 Recarregar Página</button>
                <button onclick="testarFuncionalidade()">🧪 Testar JavaScript</button>
            </div>
            
            <div id="resultado" style="margin-top: 20px;"></div>
        </div>
        
        <script>
            function testarFuncionalidade() {
                const resultado = document.getElementById('resultado');
                resultado.innerHTML = `
                    <div class="status">
                        <strong>🎉 JavaScript Funcionando!</strong><br>
                        Timestamp: ${new Date().toLocaleString('pt-BR')}<br>
                        O servidor está servindo corretamente arquivos HTML com JavaScript.
                    </div>
                `;
            }
            
            // Mostrar informações da página
            document.addEventListener('DOMContentLoaded', function() {
                console.log('WebServerManager Demo carregado com sucesso!');
                console.log('URL atual:', window.location.href);
                console.log('User Agent:', navigator.userAgent);
            });
        </script>
    </body>
    </html>
    """, encoding='utf-8')
    
    return web_dir


def main():
    """Função principal da demonstração."""
    print("🌐 Demo WebServerManager - Servidor Web Integrado")
    print("=" * 50)
    
    # Criar conteúdo de demonstração
    print("📁 Criando conteúdo HTML de demonstração...")
    web_dir = criar_conteudo_demo()
    
    # Configurar servidor
    config = ConfiguracaoServidorWeb(
        porta_preferencial=8080,
        portas_alternativas=[8081, 8082, 8083, 8084],
        diretorio_html=str(web_dir),
        modo_debug=True,
        cors_habilitado=True,
        timeout_servidor=30
    )
    
    print(f"⚙️  Configuração do servidor:")
    print(f"   - Porta preferencial: {config.porta_preferencial}")
    print(f"   - Portas alternativas: {config.portas_alternativas}")
    print(f"   - Diretório HTML: {config.diretorio_html}")
    print(f"   - Modo debug: {config.modo_debug}")
    print(f"   - CORS habilitado: {config.cors_habilitado}")
    
    # Inicializar WebServerManager
    print("\n🚀 Inicializando WebServerManager...")
    manager = WebServerManager(config)
    
    try:
        # Iniciar servidor
        url = manager.iniciar_servidor()
        print(f"✅ Servidor iniciado com sucesso!")
        print(f"🌐 URL: {url}")
        print(f"🔌 Porta: {manager.obter_porta()}")
        
        # Mostrar estatísticas
        stats = manager.obter_estatisticas()
        print(f"\n📊 Estatísticas do servidor:")
        for chave, valor in stats.items():
            print(f"   - {chave}: {valor}")
        
        print(f"\n🎯 Acesse {url} no seu navegador para ver a demonstração!")
        print("⏱️  O servidor ficará ativo por 30 segundos...")
        
        # Manter servidor ativo por um tempo
        for i in range(30, 0, -1):
            print(f"\r⏳ Tempo restante: {i:2d}s (Ctrl+C para parar)", end="", flush=True)
            time.sleep(1)
        
        print(f"\n\n⏹️  Parando servidor...")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Interrompido pelo usuário. Parando servidor...")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        
    finally:
        # Parar servidor
        manager.parar_servidor()
        print("✅ Servidor parado com sucesso!")
        
        # Limpar arquivos de demonstração
        import shutil
        if web_dir.exists():
            shutil.rmtree(web_dir)
            print("🧹 Arquivos de demonstração removidos.")
        
        print("\n🎉 Demonstração concluída!")


if __name__ == "__main__":
    main()