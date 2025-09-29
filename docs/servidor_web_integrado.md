# Sistema de Servidor Web Integrado

## Visão Geral

O Sistema de Servidor Web Integrado é uma solução completa que permite hospedar conteúdo HTML localmente e exibi-lo através de um WebView integrado ao TopSidebarContainer. O sistema inclui sincronização de dados em tempo real, inicialmente usando JSON e preparado para evolução para MySQL.

## Características Principais

- **Servidor Web Local**: Hospeda arquivos HTML estáticos com descoberta automática de portas
- **WebView Integrado**: Exibe conteúdo web dentro da aplicação Flet
- **Sincronização em Tempo Real**: Atualiza dados automaticamente entre aplicação e WebView
- **Tratamento Robusto de Erros**: Recuperação automática e fallbacks inteligentes
- **Configuração Flexível**: Sistema de configuração abrangente e validado
- **Interface em Português**: Todas as mensagens e documentação em português brasileiro

## Arquitetura do Sistema

### Componentes Principais

1. **WebServerManager**: Gerencia o servidor HTTP local
2. **WebViewComponent**: Componente Flet que encapsula o WebView
3. **DataSyncManager**: Coordena a sincronização de dados
4. **JSONDataProvider**: Provedor de dados usando arquivos JSON
5. **ConfiguracaoServidorWeb**: Sistema de configuração flexível

### Fluxo de Dados

```
TopSidebarContainer → DataSyncManager → JSONDataProvider → Arquivo JSON
                                    ↓
WebView ← JavaScript ← Polling/WebSocket ← Servidor Web Local
```

## Instalação e Configuração

### Requisitos

- Python 3.8+
- Flet 0.10+
- Dependências listadas em requirements.txt

### Configuração Básica

```python
from services.web_server import ConfiguracaoServidorWeb
from views.components.top_sidebar_container import TopSidebarContainer

# Criar configuração
config = ConfiguracaoServidorWeb(
    porta_preferencial=8080,
    diretorio_html="web_content",
    modo_debug=True
)

# Integrar ao TopSidebarContainer
container = TopSidebarContainer(
    page=page,
    habilitar_webview=True,
    config_servidor=config
)
```## Uso Deta
lhado

### Inicialização Manual do Servidor

```python
from services.web_server.server_manager import WebServerManager
from services.web_server.sync_manager import DataSyncManager
from services.web_server.data_provider import JSONDataProvider

# Criar e inicializar servidor
config = ConfiguracaoServidorWeb(porta_preferencial=8080)
server_manager = WebServerManager(config)
url_servidor = server_manager.iniciar_servidor()

print(f"Servidor iniciado em: {url_servidor}")
```

### Sincronização de Dados

```python
# Configurar sincronização
json_provider = JSONDataProvider(arquivo_json="data/sync.json")
sync_manager = DataSyncManager(json_provider)

# Atualizar dados
dados = {
    "time_tracker": {
        "tempo_decorrido": 3600,
        "esta_executando": True,
        "projeto_atual": "Meu Projeto"
    },
    "notificacoes": {
        "total": 5,
        "nao_lidas": 2
    }
}

sync_manager.atualizar_dados(dados)
```

### Integração com WebView

```python
from views.components.webview_component import WebViewComponent

# Criar WebView
webview = WebViewComponent(
    page=page,
    url_servidor=url_servidor,
    modo_debug=True
)

# Notificar atualizações
webview.notificar_atualizacao_dados(dados)
```

## Configuração Avançada

### Opções de Configuração

```python
config = ConfiguracaoServidorWeb(
    # Servidor
    porta_preferencial=8080,
    portas_alternativas=[8081, 8082, 8083],
    host="localhost",
    timeout_servidor=30,
    
    # Arquivos
    diretorio_html="web_content",
    arquivo_sincronizacao="data/sync.json",
    
    # Sincronização
    intervalo_debounce=0.3,
    intervalo_sincronizacao=1.0,
    max_tentativas_retry=3,
    delay_retry=1.0,
    
    # Segurança
    cors_habilitado=True,
    cors_origens=["http://localhost:3000"],
    permitir_directory_listing=False,
    max_tamanho_upload=10 * 1024 * 1024,  # 10MB
    
    # Debug e Logs
    modo_debug=False,
    nivel_log="INFO",
    arquivo_log="logs/servidor_web.log",
    
    # Performance
    cache_habilitado=True,
    compressao_habilitada=True,
    pool_threads=4
)
```

### Configurações Predefinidas

```python
from services.web_server import (
    criar_configuracao_desenvolvimento,
    criar_configuracao_producao
)

# Para desenvolvimento
config_dev = criar_configuracao_desenvolvimento()

# Para produção
config_prod = criar_configuracao_producao()
```

## Estrutura de Arquivos Web

### Organização Recomendada

```
web_content/
├── index.html              # Página principal
├── css/
│   ├── styles.css         # Estilos principais
│   ├── responsive.css     # Estilos responsivos
│   └── themes.css         # Temas da aplicação
├── js/
│   ├── main.js           # JavaScript principal
│   ├── sync.js           # Sincronização de dados
│   ├── utils.js          # Utilitários
│   └── components.js     # Componentes reutilizáveis
├── data/
│   └── sync.json         # Arquivo de sincronização
├── assets/
│   ├── images/           # Imagens
│   ├── icons/            # Ícones
│   └── fonts/            # Fontes personalizadas
└── templates/
    ├── error.html        # Página de erro
    └── loading.html      # Página de carregamento
```

### Exemplo de HTML com Sincronização

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aplicação Integrada</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>Minha Aplicação</h1>
            <div id="status-conexao">Conectado</div>
        </header>
        
        <main>
            <section id="time-tracker">
                <h2>Rastreamento de Tempo</h2>
                <div id="tempo-decorrido">00:00:00</div>
                <div id="projeto-atual">Nenhum projeto</div>
                <div id="status-execucao">Parado</div>
            </section>
            
            <section id="notificacoes">
                <h2>Notificações</h2>
                <div id="contador-notificacoes">0</div>
                <div id="lista-notificacoes"></div>
            </section>
            
            <section id="progresso-workflow">
                <h2>Progresso do Workflow</h2>
                <div id="barra-progresso">
                    <div id="progresso-atual" style="width: 0%"></div>
                </div>
                <div id="estagio-atual">Nenhum workflow ativo</div>
            </section>
        </main>
    </div>
    
    <script src="js/sync.js"></script>
    <script src="js/main.js"></script>
</body>
</html>
```

### JavaScript para Sincronização

```javascript
// js/sync.js
class SyncManager {
    constructor() {
        this.dados = {};
        this.ultimaAtualizacao = null;
        this.intervaloSync = 1000; // 1 segundo
        this.iniciarSincronizacao();
    }
    
    iniciarSincronizacao() {
        setInterval(() => {
            this.buscarDados();
        }, this.intervaloSync);
    }
    
    async buscarDados() {
        try {
            const response = await fetch('/data/sync.json');
            const dados = await response.json();
            
            if (dados.timestamp !== this.ultimaAtualizacao) {
                this.dados = dados.dados;
                this.ultimaAtualizacao = dados.timestamp;
                this.atualizarInterface();
            }
        } catch (error) {
            console.error('Erro na sincronização:', error);
            this.mostrarErroConexao();
        }
    }
    
    atualizarInterface() {
        // Atualizar time tracker
        if (this.dados.time_tracker) {
            this.atualizarTimeTracker(this.dados.time_tracker);
        }
        
        // Atualizar notificações
        if (this.dados.notificacoes) {
            this.atualizarNotificacoes(this.dados.notificacoes);
        }
        
        // Atualizar workflow
        if (this.dados.workflow) {
            this.atualizarWorkflow(this.dados.workflow);
        }
        
        // Atualizar status de conexão
        this.mostrarConexaoOk();
    }
    
    atualizarTimeTracker(dados) {
        const tempoElement = document.getElementById('tempo-decorrido');
        const projetoElement = document.getElementById('projeto-atual');
        const statusElement = document.getElementById('status-execucao');
        
        if (tempoElement) {
            tempoElement.textContent = this.formatarTempo(dados.tempo_decorrido);
        }
        
        if (projetoElement) {
            projetoElement.textContent = dados.projeto_atual || 'Nenhum projeto';
        }
        
        if (statusElement) {
            const status = dados.esta_executando ? 'Executando' : 
                          dados.esta_pausado ? 'Pausado' : 'Parado';
            statusElement.textContent = status;
            statusElement.className = `status-${status.toLowerCase()}`;
        }
    }
    
    atualizarNotificacoes(dados) {
        const contadorElement = document.getElementById('contador-notificacoes');
        const listaElement = document.getElementById('lista-notificacoes');
        
        if (contadorElement) {
            contadorElement.textContent = dados.nao_lidas || 0;
            contadorElement.className = dados.nao_lidas > 0 ? 'tem-notificacoes' : '';
        }
        
        if (listaElement && dados.lista) {
            listaElement.innerHTML = dados.lista
                .slice(0, 5) // Mostrar apenas as 5 mais recentes
                .map(notif => `
                    <div class="notificacao ${notif.lida ? 'lida' : 'nao-lida'}">
                        <div class="titulo">${notif.titulo}</div>
                        <div class="data">${this.formatarData(notif.data)}</div>
                    </div>
                `).join('');
        }
    }
    
    atualizarWorkflow(dados) {
        const progressoElement = document.getElementById('progresso-atual');
        const estagioElement = document.getElementById('estagio-atual');
        
        if (progressoElement) {
            progressoElement.style.width = `${dados.progresso || 0}%`;
        }
        
        if (estagioElement) {
            estagioElement.textContent = dados.estagio_atual || 'Nenhum workflow ativo';
        }
    }
    
    formatarTempo(segundos) {
        const horas = Math.floor(segundos / 3600);
        const minutos = Math.floor((segundos % 3600) / 60);
        const segs = segundos % 60;
        
        return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
    }
    
    formatarData(timestamp) {
        return new Date(timestamp).toLocaleString('pt-BR');
    }
    
    mostrarConexaoOk() {
        const statusElement = document.getElementById('status-conexao');
        if (statusElement) {
            statusElement.textContent = 'Conectado';
            statusElement.className = 'conectado';
        }
    }
    
    mostrarErroConexao() {
        const statusElement = document.getElementById('status-conexao');
        if (statusElement) {
            statusElement.textContent = 'Erro de Conexão';
            statusElement.className = 'erro-conexao';
        }
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.syncManager = new SyncManager();
});
```

## Tratamento de Erros

### Tipos de Erro

O sistema define uma hierarquia de exceções específicas:

```python
from services.web_server.exceptions import (
    ServidorWebError,           # Erros do servidor web
    WebViewError,               # Erros do WebView
    SincronizacaoError,         # Erros de sincronização
    RecursoIndisponivelError,   # Recursos não disponíveis
    ConfiguracaoInvalidaError   # Configuração inválida
)
```

### Estratégias de Recuperação

1. **Falha na Inicialização do Servidor**
   - Tentativa automática em portas alternativas
   - Modo fallback sem WebView
   - Mensagens de erro em português

2. **Erro de Sincronização**
   - Retry automático com backoff exponencial
   - Cache local dos últimos dados válidos
   - Notificação visual do status

3. **Falha no WebView**
   - Recarregamento automático após timeout
   - Página de erro personalizada
   - Logs detalhados para debug

### Exemplo de Tratamento

```python
try:
    # Inicializar sistema
    server_manager = WebServerManager(config)
    url = server_manager.iniciar_servidor()
    
except RecursoIndisponivelError as e:
    print(f"Erro: {e.mensagem}")
    print("Sugestão: Verifique se as portas estão disponíveis")
    
except ServidorWebError as e:
    print(f"Erro no servidor: {e.mensagem}")
    print(f"Código: {e.codigo_erro}")
    
except Exception as e:
    print(f"Erro inesperado: {e}")
    # Log detalhado para debug
    import traceback
    traceback.print_exc()
```

## Monitoramento e Debug

### Logs Detalhados

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/servidor_web.log'),
        logging.StreamHandler()
    ]
)

# Usar com modo debug
config = ConfiguracaoServidorWeb(
    modo_debug=True,
    nivel_log="DEBUG"
)
```

### Diagnóstico de Configuração

```python
from services.web_server import diagnosticar_configuracao

# Executar diagnóstico
diagnostico = diagnosticar_configuracao(config)

print(f"Configuração válida: {diagnostico['configuracao_valida']}")
print(f"Erros: {len(diagnostico['erros'])}")
print(f"Avisos: {len(diagnostico['avisos'])}")

for erro in diagnostico['erros']:
    print(f"❌ {erro}")

for aviso in diagnostico['avisos']:
    print(f"⚠️ {aviso}")
```

### Métricas de Performance

```python
# Monitorar latência de sincronização
import time

start_time = time.perf_counter()
sync_manager.atualizar_dados(dados)
end_time = time.perf_counter()

latencia = (end_time - start_time) * 1000  # ms
print(f"Latência de sincronização: {latencia:.2f}ms")

# Monitorar uso de memória
import psutil
import os

process = psutil.Process(os.getpid())
memoria_mb = process.memory_info().rss / 1024 / 1024
print(f"Uso de memória: {memoria_mb:.1f}MB")
```

## Migração para MySQL

### Preparação

O sistema está preparado para migração futura de JSON para MySQL:

```python
from services.web_server.mysql_provider import MySQLDataProvider

# Configuração MySQL (futura)
mysql_config = {
    'host': 'localhost',
    'port': 3306,
    'database': 'app_data',
    'user': 'app_user',
    'password': 'app_password'
}

# Usar MySQL provider (quando implementado)
mysql_provider = MySQLDataProvider(mysql_config)
sync_manager = DataSyncManager(mysql_provider)
```

### Estrutura de Tabelas

```sql
-- Tabela principal de dados sincronizados
CREATE TABLE dados_sincronizacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chave VARCHAR(255) NOT NULL,
    dados JSON NOT NULL,
    versao INT NOT NULL DEFAULT 1,
    timestamp_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timestamp_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_chave (chave),
    INDEX idx_timestamp (timestamp_atualizacao)
);

-- Tabela de histórico de mudanças
CREATE TABLE historico_sincronizacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chave VARCHAR(255) NOT NULL,
    dados_anteriores JSON,
    dados_novos JSON NOT NULL,
    versao_anterior INT,
    versao_nova INT NOT NULL,
    timestamp_mudanca TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chave_timestamp (chave, timestamp_mudanca)
);
```

## Testes e Qualidade

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/test_servidor_web_*.py -v

# Testes de integração
python -m pytest tests/test_servidor_web_integracao_completa.py -v

# Testes de performance
python -m pytest tests/test_servidor_web_performance.py -v

# Testes de cenários de erro
python -m pytest tests/test_servidor_web_cenarios_erro.py -v
```

### Cobertura de Testes

```bash
# Instalar coverage
pip install coverage

# Executar com cobertura
coverage run -m pytest tests/test_servidor_web_*.py
coverage report
coverage html  # Gerar relatório HTML
```

### Benchmarks de Performance

```python
# Executar benchmarks
python tests/test_servidor_web_performance.py

# Resultados esperados:
# - Inicialização do servidor: < 1s
# - Latência de sincronização: < 100ms
# - Throughput: > 50 updates/segundo
# - Uso de memória: < 50MB delta
```

## Solução de Problemas

### Problemas Comuns

1. **Porta já em uso**
   ```
   Erro: RecursoIndisponivelError - Porta 8080 já está em uso
   Solução: Configure portas alternativas ou pare o processo que usa a porta
   ```

2. **Arquivo de sincronização corrompido**
   ```
   Erro: SincronizacaoError - Arquivo JSON inválido
   Solução: Delete o arquivo sync.json (será recriado automaticamente)
   ```

3. **WebView não carrega**
   ```
   Erro: WebViewError - Falha no carregamento
   Solução: Verifique se o servidor está ativo e a URL está correta
   ```

4. **Sincronização lenta**
   ```
   Problema: Latência alta na sincronização
   Solução: Ajuste intervalo_debounce e intervalo_sincronizacao
   ```

### Logs de Debug

```python
# Habilitar logs detalhados
config = ConfiguracaoServidorWeb(
    modo_debug=True,
    nivel_log="DEBUG"
)

# Verificar logs
tail -f logs/servidor_web.log
```

### Verificação de Saúde

```python
from services.web_server import verificar_saude_sistema

# Executar verificação completa
resultado = verificar_saude_sistema(config)

print(f"Sistema saudável: {resultado['saudavel']}")
for problema in resultado['problemas']:
    print(f"⚠️ {problema}")
```

## Exemplos Práticos

### Exemplo Básico

Veja `examples/servidor_web_demo.py` para um exemplo completo de uso.

### Exemplo com TopSidebarContainer

```python
import flet as ft
from views.components.top_sidebar_container import TopSidebarContainer
from services.web_server import ConfiguracaoServidorWeb

def main(page: ft.Page):
    # Configurar página
    page.title = "Aplicação com WebView Integrado"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Configurar servidor web
    config = ConfiguracaoServidorWeb(
        porta_preferencial=8080,
        diretorio_html="web_content",
        modo_debug=True
    )
    
    # Criar container com WebView habilitado
    container = TopSidebarContainer(
        page=page,
        habilitar_webview=True,
        config_servidor=config
    )
    
    # Adicionar à página
    page.add(container)

if __name__ == '__main__':
    ft.app(target=main)
```

### Exemplo de Customização

```python
# Customizar comportamento do WebView
class MeuWebViewComponent(WebViewComponent):
    def on_page_started(self, e):
        print("Página iniciou carregamento")
        super().on_page_started(e)
    
    def on_page_ended(self, e):
        print("Página terminou carregamento")
        super().on_page_ended(e)
        
        # Executar JavaScript personalizado
        self.executar_javascript("""
            console.log('WebView carregado com sucesso!');
            document.body.style.fontFamily = 'Arial, sans-serif';
        """)

# Usar componente customizado
webview_customizado = MeuWebViewComponent(
    page=page,
    url_servidor=url_servidor
)
```

## Contribuição

### Estrutura do Código

```
services/web_server/
├── __init__.py              # Exports principais
├── server_manager.py        # Gerenciador do servidor HTTP
├── sync_manager.py          # Gerenciador de sincronização
├── data_provider.py         # Provedores de dados (JSON/MySQL)
├── models.py               # Modelos de dados
├── exceptions.py           # Exceções personalizadas
├── config.py               # Sistema de configuração
└── utils.py                # Utilitários

views/components/
├── webview_component.py     # Componente WebView
└── top_sidebar_container.py # Container principal

tests/
├── test_servidor_web_integracao_completa.py
├── test_servidor_web_performance.py
└── test_servidor_web_cenarios_erro.py
```

### Diretrizes de Desenvolvimento

1. **Código em Português**: Comentários, variáveis e documentação
2. **Testes Abrangentes**: Cobertura mínima de 90%
3. **Tratamento de Erros**: Sempre em português com códigos específicos
4. **Performance**: Latência < 100ms, throughput > 50 ops/s
5. **Compatibilidade**: Python 3.8+ e Flet 0.10+

### Adicionando Novos Recursos

1. Implemente a funcionalidade
2. Adicione testes unitários e de integração
3. Atualize a documentação
4. Execute todos os testes
5. Verifique performance e cobertura

## Licença

Este sistema é parte do projeto principal e segue a mesma licença.

## Suporte

Para dúvidas ou problemas:

1. Consulte esta documentação
2. Execute diagnósticos: `diagnosticar_configuracao(config)`
3. Verifique logs: `logs/servidor_web.log`
4. Execute testes: `pytest tests/test_servidor_web_*.py`

---

**Versão da Documentação**: 1.0.0  
**Última Atualização**: Dezembro 2024