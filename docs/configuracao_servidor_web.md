# Sistema de Configuração do Servidor Web Integrado

Este documento descreve como usar o sistema de configuração flexível do servidor web integrado, incluindo validação, carregamento de arquivos JSON e funcionalidades de debug.

## Visão Geral

O sistema de configuração fornece uma interface unificada para gerenciar todas as configurações do servidor web, incluindo:

- Configurações de rede (porta, host, timeout)
- Configurações de CORS e segurança
- Configurações de logging e debug
- Configurações de sincronização de dados
- Configurações de cache e performance

## Uso Básico

### Criando uma Configuração Padrão

```python
from services.web_server import ConfiguracaoServidorWeb

# Criar configuração com valores padrão
config = ConfiguracaoServidorWeb()

print(f"Porta: {config.porta_preferencial}")  # 8080
print(f"Host: {config.host}")                 # localhost
print(f"Debug: {config.modo_debug}")          # False
```

### Criando uma Configuração Personalizada

```python
config = ConfiguracaoServidorWeb(
    porta_preferencial=8085,
    modo_debug=True,
    nivel_log="DEBUG",
    cors_origens=["http://localhost:3000", "http://127.0.0.1:3000"],
    diretorio_html="meu_web_content",
    intervalo_sincronizacao=0.5
)
```

## Salvamento e Carregamento de Arquivos

### Salvar Configuração em Arquivo JSON

```python
config = ConfiguracaoServidorWeb(
    porta_preferencial=8085,
    modo_debug=True
)

# Salvar em arquivo
config.salvar_arquivo("config.json")
```

### Carregar Configuração de Arquivo JSON

```python
# Carregar configuração existente
config = ConfiguracaoServidorWeb.carregar_arquivo("config.json")

# Carregar com fallback (cria arquivo se não existir)
config = ConfiguracaoServidorWeb.carregar_com_fallback(
    "config.json", 
    criar_se_nao_existir=True
)
```

## Gerenciamento Avançado com ConfigManager

O `ConfigManager` fornece funcionalidades avançadas como monitoramento de mudanças e callbacks:

```python
from services.web_server import ConfigManager

def callback_mudanca(nova_config):
    print(f"Configuração atualizada! Nova porta: {nova_config.porta_preferencial}")

# Criar manager com monitoramento
manager = ConfigManager(
    caminho_config="config.json",
    monitorar_mudancas=True,
    callback_mudanca=callback_mudanca
)

# Obter configuração atual
config = manager.obter_configuracao()

# Atualizar configuração
sucesso = manager.atualizar_configuracao(
    porta_preferencial=8090,
    modo_debug=True
)

# Obter informações do manager
info = manager.obter_info_configuracao()
print(info)
```

## Validação e Diagnóstico

### Validação Automática

Todas as configurações são validadas automaticamente:

```python
try:
    config = ConfiguracaoServidorWeb(
        porta_preferencial=100  # Porta inválida
    )
except ErroValidacaoConfiguracao as e:
    print(f"Erro de validação: {e}")
```

### Diagnóstico Completo

```python
from services.web_server import diagnosticar_configuracao, gerar_relatorio_configuracao

config = ConfiguracaoServidorWeb()

# Executar diagnóstico
diagnostico = diagnosticar_configuracao(config)

print(f"Válida: {diagnostico['configuracao_valida']}")
print(f"Erros: {len(diagnostico['erros'])}")
print(f"Avisos: {len(diagnostico['avisos'])}")

# Gerar relatório detalhado
relatorio = gerar_relatorio_configuracao(config)
print(relatorio)
```

## Configurações Predefinidas

### Configuração para Desenvolvimento

```python
from services.web_server import criar_configuracao_desenvolvimento

config_dev = criar_configuracao_desenvolvimento()
# Debug habilitado, cache desabilitado, logs detalhados
```

### Configuração para Produção

```python
from services.web_server import criar_configuracao_producao

config_prod = criar_configuracao_producao()
# Debug desabilitado, cache habilitado, logs otimizados
```

## Utilitários de Rede

### Verificar Porta Disponível

```python
from services.web_server import verificar_porta_disponivel, encontrar_porta_disponivel

# Verificar porta específica
disponivel = verificar_porta_disponivel(8080)

# Encontrar primeira porta disponível em um intervalo
porta = encontrar_porta_disponivel(8080, 8090)
```

## Carregamento de Variáveis de Ambiente

```python
import os
from services.web_server import carregar_configuracao_do_ambiente

# Definir variáveis de ambiente
os.environ['SERVIDOR_WEB_PORTA'] = '8085'
os.environ['SERVIDOR_WEB_DEBUG'] = 'true'
os.environ['SERVIDOR_WEB_HOST'] = 'example.com'

# Carregar configuração
config = carregar_configuracao_do_ambiente()
```

### Variáveis de Ambiente Suportadas

- `SERVIDOR_WEB_PORTA`: Porta preferencial
- `SERVIDOR_WEB_HOST`: Host do servidor
- `SERVIDOR_WEB_DEBUG`: Modo debug (true/false)
- `SERVIDOR_WEB_DIRETORIO_HTML`: Diretório HTML
- `SERVIDOR_WEB_NIVEL_LOG`: Nível de log
- `SERVIDOR_WEB_ARQUIVO_LOG`: Arquivo de log
- `SERVIDOR_WEB_CORS_HABILITADO`: CORS habilitado (true/false)

## Interface de Linha de Comando

O sistema inclui uma CLI para gerenciamento de configurações:

### Validar Configuração

```bash
python -m services.web_server.config_cli validar config.json
```

### Criar Configuração

```bash
# Configuração padrão
python -m services.web_server.config_cli criar --tipo padrao config.json

# Configuração de desenvolvimento
python -m services.web_server.config_cli criar --tipo desenvolvimento config.json

# Configuração de produção
python -m services.web_server.config_cli criar --tipo producao config.json
```

### Diagnosticar Configuração

```bash
# Relatório detalhado
python -m services.web_server.config_cli diagnosticar config.json

# Saída JSON
python -m services.web_server.config_cli diagnosticar --formato json config.json
```

### Exportar como Variáveis de Ambiente

```bash
# Para stdout
python -m services.web_server.config_cli exportar-env config.json

# Para arquivo
python -m services.web_server.config_cli exportar-env --saida .env config.json
```

## Configurações Principais

### Configurações de Rede

- `porta_preferencial`: Porta preferencial do servidor (padrão: 8080)
- `porta_minima`: Porta mínima do intervalo (padrão: 8080)
- `porta_maxima`: Porta máxima do intervalo (padrão: 8090)
- `host`: Host do servidor (padrão: "localhost")
- `timeout_servidor`: Timeout em segundos (padrão: 30)

### Configurações de Diretórios

- `diretorio_html`: Diretório dos arquivos HTML (padrão: "web_content")
- `diretorio_dados`: Diretório de dados (padrão: "web_content/data")
- `arquivo_index`: Arquivo index (padrão: "index.html")

### Configurações de CORS

- `cors_habilitado`: CORS habilitado (padrão: True)
- `cors_origens`: Lista de origens permitidas (padrão: ["*"])
- `cors_metodos`: Métodos HTTP permitidos
- `cors_cabecalhos`: Cabeçalhos permitidos
- `cors_credenciais`: Permitir credenciais (padrão: False)

### Configurações de Segurança

- `validar_caminhos`: Validar caminhos de arquivos (padrão: True)
- `permitir_directory_listing`: Permitir listagem de diretórios (padrão: False)
- `max_tamanho_upload`: Tamanho máximo de upload em bytes (padrão: 10MB)
- `tipos_arquivo_permitidos`: Lista de extensões permitidas

### Configurações de Logging

- `modo_debug`: Modo debug (padrão: False)
- `nivel_log`: Nível de log (padrão: "INFO")
- `arquivo_log`: Arquivo de log (padrão: None)
- `log_formato`: Formato das mensagens de log
- `log_rotacao`: Rotação de logs (padrão: True)
- `log_max_bytes`: Tamanho máximo do arquivo de log (padrão: 10MB)
- `log_backup_count`: Número de backups (padrão: 5)

### Configurações de Sincronização

- `intervalo_sincronizacao`: Intervalo de sincronização em segundos (padrão: 1.0)
- `debounce_delay`: Delay de debounce em segundos (padrão: 0.5)
- `max_tentativas_retry`: Máximo de tentativas de retry (padrão: 3)
- `delay_retry`: Delay entre tentativas em segundos (padrão: 1.0)

### Configurações de Performance

- `cache_habilitado`: Cache habilitado (padrão: True)
- `cache_max_age`: Idade máxima do cache em segundos (padrão: 3600)
- `compressao_habilitada`: Compressão habilitada (padrão: True)
- `keep_alive`: Keep-alive habilitado (padrão: True)

## Tratamento de Erros

O sistema define exceções específicas para diferentes tipos de erro:

- `ErroConfiguracaoServidorWeb`: Exceção base
- `ErroValidacaoConfiguracao`: Erro de validação
- `ErroCarregamentoConfiguracao`: Erro no carregamento de arquivo

```python
from services.web_server import (
    ErroConfiguracaoServidorWeb,
    ErroValidacaoConfiguracao,
    ErroCarregamentoConfiguracao
)

try:
    config = ConfiguracaoServidorWeb.carregar_arquivo("config_inexistente.json")
except ErroCarregamentoConfiguracao as e:
    print(f"Erro ao carregar: {e}")
except ErroValidacaoConfiguracao as e:
    print(f"Erro de validação: {e}")
except ErroConfiguracaoServidorWeb as e:
    print(f"Erro geral: {e}")
```

## Exemplo Completo

```python
from services.web_server import (
    ConfigManager,
    diagnosticar_configuracao,
    verificar_porta_disponivel
)

def configurar_servidor():
    # Criar manager de configuração
    manager = ConfigManager(
        caminho_config="servidor_config.json",
        monitorar_mudancas=True
    )
    
    # Obter configuração
    config = manager.obter_configuracao()
    
    # Verificar se porta está disponível
    if not verificar_porta_disponivel(config.porta_preferencial):
        print(f"Porta {config.porta_preferencial} não disponível")
        # Atualizar para porta disponível
        from services.web_server import encontrar_porta_disponivel
        nova_porta = encontrar_porta_disponivel(8080, 8090)
        if nova_porta:
            manager.atualizar_configuracao(porta_preferencial=nova_porta)
            print(f"Usando porta alternativa: {nova_porta}")
    
    # Executar diagnóstico
    diagnostico = diagnosticar_configuracao(config)
    if not diagnostico['configuracao_valida']:
        print("⚠️ Problemas encontrados na configuração:")
        for erro in diagnostico['erros']:
            print(f"  - {erro}")
    
    return manager.obter_configuracao()

# Usar a configuração
config = configurar_servidor()
print(f"Servidor configurado na porta {config.porta_preferencial}")
```

## Integração com TopSidebarContainer

Para usar o sistema de configuração com o TopSidebarContainer:

```python
from services.web_server import obter_configuracao
from views.components.top_sidebar_container import TopSidebarContainer

# Obter configuração
config = obter_configuracao()

# Criar TopSidebarContainer com configuração
container = TopSidebarContainer(
    page=page,
    habilitar_webview=True,
    config_servidor=config
)
```

Este sistema de configuração fornece uma base sólida e flexível para gerenciar todas as configurações do servidor web integrado, com validação robusta, diagnóstico detalhado e suporte a diferentes ambientes de execução.