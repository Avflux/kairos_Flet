# Guia de Migração: JSON para MySQL

## Visão Geral

Este documento descreve o processo completo de migração do sistema de sincronização de dados do formato JSON para banco de dados MySQL. A migração foi projetada para ser segura, reversível e com mínima interrupção do serviço.

## Pré-requisitos

### Requisitos de Sistema

- **Python 3.8+** com as dependências do projeto instaladas
- **MySQL Server 5.7+** ou **MariaDB 10.3+**
- **Acesso administrativo** ao banco de dados MySQL
- **Backup** dos dados JSON existentes

### Dependências Python Adicionais

```bash
pip install mysql-connector-python
# ou
pip install PyMySQL
```

### Configuração do MySQL

1. **Criar banco de dados:**
```sql
CREATE DATABASE servidor_web_integrado 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

2. **Criar usuário dedicado:**
```sql
CREATE USER 'servidor_web_user'@'localhost' 
IDENTIFIED BY 'senha_segura_aqui';

GRANT ALL PRIVILEGES ON servidor_web_integrado.* 
TO 'servidor_web_user'@'localhost';

FLUSH PRIVILEGES;
```

3. **Verificar configuração:**
```sql
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'servidor_web_user';
```

## Estrutura do Banco de Dados

### Tabelas Principais

#### 1. dados_sincronizacao
```sql
CREATE TABLE dados_sincronizacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dados JSON NOT NULL,
    versao INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    INDEX idx_versao (versao),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 2. log_sincronizacao
```sql
CREATE TABLE log_sincronizacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operacao VARCHAR(50) NOT NULL,
    dados_antes JSON,
    dados_depois JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100),
    ip_origem VARCHAR(45),
    INDEX idx_operacao (operacao),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3. configuracao_sistema
```sql
CREATE TABLE configuracao_sistema (
    chave VARCHAR(100) PRIMARY KEY,
    valor JSON NOT NULL,
    descricao TEXT,
    timestamp_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## Processo de Migração

### Fase 1: Preparação

#### 1.1 Backup dos Dados Atuais
```python
import shutil
from datetime import datetime
from pathlib import Path

def criar_backup_json():
    """Cria backup dos dados JSON antes da migração."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Diretórios
    origem = Path("web_content/data")
    destino = Path(f"data/backup/json_backup_{timestamp}")
    
    # Criar backup
    if origem.exists():
        shutil.copytree(origem, destino)
        print(f"Backup criado em: {destino}")
        return destino
    else:
        raise FileNotFoundError("Diretório de dados JSON não encontrado")

# Executar backup
backup_path = criar_backup_json()
```

#### 1.2 Validação dos Dados JSON
```python
import json
from pathlib import Path

def validar_dados_json(caminho_arquivo):
    """Valida integridade dos dados JSON."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Validações básicas
        if not isinstance(dados, dict):
            raise ValueError("Dados devem ser um objeto JSON")
        
        # Validar estrutura esperada
        campos_obrigatorios = ['timestamp', 'versao']
        for campo in campos_obrigatorios:
            if campo not in dados:
                print(f"Aviso: Campo '{campo}' não encontrado")
        
        print(f"Dados JSON válidos: {len(dados)} campos encontrados")
        return dados
        
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}")
    except Exception as e:
        raise ValueError(f"Erro na validação: {e}")

# Validar dados
dados = validar_dados_json("web_content/data/sync.json")
```

### Fase 2: Configuração

#### 2.1 Configuração do Sistema
```python
from services.web_server.config import ConfiguracaoServidorWeb, ConfiguracaoMySQL

# Criar configuração MySQL
config_mysql = ConfiguracaoMySQL(
    host="localhost",
    porta=3306,
    usuario="servidor_web_user",
    senha="senha_segura_aqui",
    banco_dados="servidor_web_integrado",
    pool_size=10,
    ssl_habilitado=True  # Recomendado para produção
)

# Atualizar configuração principal
config_sistema = ConfiguracaoServidorWeb()
config_sistema.tipo_provedor = "mysql"
config_sistema.configuracao_mysql = config_mysql

# Salvar configuração
config_sistema.salvar_arquivo("config/servidor_web_mysql.json")
```

#### 2.2 Teste de Conectividade
```python
from services.web_server.mysql_provider import MySQLDataProvider

def testar_conexao_mysql(config_mysql):
    """Testa conexão com MySQL antes da migração."""
    try:
        provider = MySQLDataProvider(config_mysql)
        provider.conectar()
        
        if provider.verificar_conexao():
            print("✓ Conexão MySQL estabelecida com sucesso")
            provider.desconectar()
            return True
        else:
            print("✗ Falha na verificação de conexão")
            return False
            
    except Exception as e:
        print(f"✗ Erro na conexão: {e}")
        return False

# Testar conexão
if testar_conexao_mysql(config_mysql):
    print("Sistema pronto para migração")
else:
    print("Corrigir problemas de conexão antes de continuar")
```

### Fase 3: Migração dos Dados

#### 3.1 Migração Automática
```python
from services.web_server.data_provider_factory import migrar_json_para_mysql

def executar_migracao_completa():
    """Executa migração completa de JSON para MySQL."""
    try:
        print("Iniciando migração JSON → MySQL...")
        
        # Configurações
        config_json = {
            "caminho_arquivo": "web_content/data/sync.json",
            "intervalo_observacao": 1.0
        }
        
        config_mysql = {
            "host": "localhost",
            "porta": 3306,
            "usuario": "servidor_web_user",
            "senha": "senha_segura_aqui",
            "banco_dados": "servidor_web_integrado"
        }
        
        # Executar migração
        migrar_json_para_mysql(config_json, config_mysql)
        
        print("✓ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro na migração: {e}")
        return False

# Executar migração
sucesso = executar_migracao_completa()
```

#### 3.2 Migração Manual (Passo a Passo)
```python
def migracao_manual_detalhada():
    """Migração manual com controle detalhado."""
    from services.web_server.json_provider import JSONDataProvider
    from services.web_server.mysql_provider import MySQLDataProvider
    
    # 1. Carregar dados do JSON
    print("1. Carregando dados JSON...")
    json_provider = JSONDataProvider("web_content/data/sync.json")
    dados_json = json_provider.carregar_dados()
    print(f"   Carregados: {len(dados_json)} registros")
    
    # 2. Conectar ao MySQL
    print("2. Conectando ao MySQL...")
    mysql_provider = MySQLDataProvider(config_mysql)
    mysql_provider.conectar()
    print("   Conexão estabelecida")
    
    # 3. Criar estrutura do banco
    print("3. Criando estrutura do banco...")
    mysql_provider.criar_tabelas()
    print("   Tabelas criadas")
    
    # 4. Migrar dados
    print("4. Migrando dados...")
    mysql_provider.salvar_dados(dados_json)
    print("   Dados migrados")
    
    # 5. Verificar integridade
    print("5. Verificando integridade...")
    dados_mysql = mysql_provider.carregar_dados()
    
    if len(dados_mysql) == len(dados_json):
        print("   ✓ Integridade verificada")
    else:
        print(f"   ✗ Inconsistência: JSON={len(dados_json)}, MySQL={len(dados_mysql)}")
        return False
    
    # 6. Finalizar
    mysql_provider.desconectar()
    print("6. Migração concluída!")
    return True

# Executar migração manual
migracao_manual_detalhada()
```

### Fase 4: Validação e Testes

#### 4.1 Testes de Integridade
```python
def validar_migracao():
    """Valida se a migração foi bem-sucedida."""
    from services.web_server.data_provider_factory import criar_provedor_dados
    
    # Configuração para MySQL
    config = {
        "tipo_provedor": "mysql",
        "mysql": {
            "host": "localhost",
            "usuario": "servidor_web_user",
            "senha": "senha_segura_aqui",
            "banco_dados": "servidor_web_integrado"
        }
    }
    
    try:
        # Criar provedor MySQL
        provider = criar_provedor_dados(config)
        
        # Testar operações básicas
        dados_teste = {"teste_migracao": True, "timestamp": "2024-01-01"}
        
        # Salvar
        provider.salvar_dados(dados_teste)
        print("✓ Salvamento funcionando")
        
        # Carregar
        dados_carregados = provider.carregar_dados()
        if "teste_migracao" in dados_carregados:
            print("✓ Carregamento funcionando")
        else:
            print("✗ Problema no carregamento")
            return False
        
        # Testar callbacks
        callback_chamado = False
        def callback_teste(dados):
            nonlocal callback_chamado
            callback_chamado = True
        
        provider.configurar_observador(callback_teste)
        provider.salvar_dados({"callback_teste": True})
        
        if callback_chamado:
            print("✓ Sistema de callbacks funcionando")
        else:
            print("✗ Problema nos callbacks")
            return False
        
        print("✓ Validação completa bem-sucedida")
        return True
        
    except Exception as e:
        print(f"✗ Erro na validação: {e}")
        return False

# Executar validação
validar_migracao()
```

#### 4.2 Testes de Performance
```python
import time
from datetime import datetime

def testar_performance_mysql():
    """Testa performance do sistema MySQL."""
    from services.web_server.data_provider_factory import criar_provedor_dados
    
    config = {
        "tipo_provedor": "mysql",
        "mysql": {
            "host": "localhost",
            "usuario": "servidor_web_user",
            "senha": "senha_segura_aqui",
            "banco_dados": "servidor_web_integrado"
        }
    }
    
    provider = criar_provedor_dados(config)
    
    # Teste de múltiplas operações
    num_operacoes = 100
    dados_teste = {"performance_test": True, "data": list(range(1000))}
    
    # Testar salvamento
    inicio = time.time()
    for i in range(num_operacoes):
        dados_teste["iteracao"] = i
        provider.salvar_dados(dados_teste)
    tempo_salvamento = time.time() - inicio
    
    # Testar carregamento
    inicio = time.time()
    for i in range(num_operacoes):
        provider.carregar_dados()
    tempo_carregamento = time.time() - inicio
    
    print(f"Performance MySQL:")
    print(f"  Salvamento: {tempo_salvamento:.2f}s ({num_operacoes} ops)")
    print(f"  Carregamento: {tempo_carregamento:.2f}s ({num_operacoes} ops)")
    print(f"  Média salvamento: {(tempo_salvamento/num_operacoes)*1000:.2f}ms/op")
    print(f"  Média carregamento: {(tempo_carregamento/num_operacoes)*1000:.2f}ms/op")

# Executar teste de performance
testar_performance_mysql()
```

### Fase 5: Atualização da Aplicação

#### 5.1 Atualizar Configuração Principal
```python
# Arquivo: main.py ou onde TopSidebarContainer é inicializado

from services.web_server.config import ConfiguracaoServidorWeb

# Carregar nova configuração
config = ConfiguracaoServidorWeb.carregar_arquivo("config/servidor_web_mysql.json")

# Inicializar TopSidebarContainer com MySQL
sidebar = TopSidebarContainer(
    page=page,
    habilitar_webview=True,
    config_servidor=config
)
```

#### 5.2 Monitoramento Inicial
```python
import logging
from datetime import datetime, timedelta

def configurar_monitoramento_migracao():
    """Configura monitoramento especial pós-migração."""
    
    # Logger específico para migração
    logger = logging.getLogger('migracao_mysql')
    handler = logging.FileHandler('logs/migracao_mysql.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    logger.info("Sistema migrado para MySQL - monitoramento iniciado")
    
    return logger

# Configurar monitoramento
logger_migracao = configurar_monitoramento_migracao()
```

## Rollback (Reversão)

### Quando Fazer Rollback

- Problemas de performance significativos
- Erros de integridade de dados
- Instabilidade do sistema
- Problemas de conectividade persistentes

### Processo de Rollback

#### 1. Parar o Sistema
```python
# Parar servidor web e sincronização
servidor.parar_servidor()
sync_manager.parar_sincronizacao()
```

#### 2. Restaurar Configuração JSON
```python
from services.web_server.config import ConfiguracaoServidorWeb

# Restaurar configuração JSON
config = ConfiguracaoServidorWeb()
config.tipo_provedor = "json"
config.caminho_arquivo_json = "web_content/data/sync.json"
config.salvar_arquivo("config/servidor_web.json")
```

#### 3. Restaurar Dados do Backup
```python
import shutil
from pathlib import Path

def restaurar_backup_json(caminho_backup):
    """Restaura dados JSON do backup."""
    backup_path = Path(caminho_backup)
    destino_path = Path("web_content/data")
    
    if backup_path.exists():
        # Remover dados atuais
        if destino_path.exists():
            shutil.rmtree(destino_path)
        
        # Restaurar backup
        shutil.copytree(backup_path, destino_path)
        print(f"Backup restaurado de: {caminho_backup}")
    else:
        raise FileNotFoundError(f"Backup não encontrado: {caminho_backup}")

# Restaurar último backup
restaurar_backup_json("data/backup/json_backup_20240101_120000")
```

#### 4. Reiniciar Sistema
```python
# Reinicializar com configuração JSON
config = ConfiguracaoServidorWeb.carregar_arquivo("config/servidor_web.json")
sidebar = TopSidebarContainer(page=page, config_servidor=config)
```

## Manutenção Pós-Migração

### Monitoramento Contínuo

#### 1. Logs de Sistema
```python
# Configurar logs detalhados
config.modo_debug = True
config.nivel_log = "DEBUG"
config.arquivo_log = "logs/servidor_web_mysql.log"
```

#### 2. Métricas de Performance
```python
def coletar_metricas_mysql():
    """Coleta métricas de performance do MySQL."""
    # TODO: Implementar coleta de métricas
    # - Tempo de resposta das queries
    # - Uso de conexões do pool
    # - Tamanho do banco de dados
    # - Frequência de sincronização
    pass
```

### Backup Automático

#### 1. Backup do Banco MySQL
```bash
#!/bin/bash
# Script: backup_mysql.sh

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="data/backup/mysql"
DB_NAME="servidor_web_integrado"

mkdir -p $BACKUP_DIR

mysqldump -u servidor_web_user -p $DB_NAME > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

#### 2. Agendamento de Backup
```python
import schedule
import time
import subprocess

def executar_backup_mysql():
    """Executa backup automático do MySQL."""
    try:
        subprocess.run(["bash", "scripts/backup_mysql.sh"], check=True)
        print("Backup MySQL executado com sucesso")
    except subprocess.CalledProcessError as e:
        print(f"Erro no backup MySQL: {e}")

# Agendar backup diário às 2:00
schedule.every().day.at("02:00").do(executar_backup_mysql)

# Loop de agendamento (executar em thread separada)
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Otimizações Avançadas

### 1. Índices de Performance
```sql
-- Índices adicionais para otimização
CREATE INDEX idx_dados_timestamp ON dados_sincronizacao(timestamp DESC);
CREATE INDEX idx_dados_versao_timestamp ON dados_sincronizacao(versao, timestamp);

-- Índice para busca em dados JSON (MySQL 5.7+)
CREATE INDEX idx_dados_json_path ON dados_sincronizacao((JSON_EXTRACT(dados, '$.usuario')));
```

### 2. Configurações MySQL Otimizadas
```sql
-- Configurações recomendadas para performance
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL innodb_log_file_size = 268435456;     -- 256MB
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 67108864;          -- 64MB
```

### 3. Pool de Conexões Avançado
```python
# Configuração otimizada do pool
config_mysql = ConfiguracaoMySQL(
    pool_size=20,           # Mais conexões para alta concorrência
    max_overflow=30,        # Overflow maior
    pool_timeout=60,        # Timeout maior
    pool_recycle=1800,      # Reciclar conexões a cada 30min
    pool_pre_ping=True      # Verificar conexões antes do uso
)
```

## Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão
```
Erro: Can't connect to MySQL server
```
**Solução:**
- Verificar se MySQL está rodando
- Confirmar credenciais de acesso
- Verificar firewall/rede
- Testar conexão manual: `mysql -u usuario -p -h host`

#### 2. Erro de Permissões
```
Erro: Access denied for user
```
**Solução:**
```sql
GRANT ALL PRIVILEGES ON servidor_web_integrado.* TO 'usuario'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. Erro de Charset
```
Erro: Incorrect string value
```
**Solução:**
```sql
ALTER DATABASE servidor_web_integrado CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE dados_sincronizacao CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4. Performance Lenta
**Diagnóstico:**
```sql
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS;
EXPLAIN SELECT * FROM dados_sincronizacao ORDER BY timestamp DESC LIMIT 1;
```

**Soluções:**
- Adicionar índices apropriados
- Otimizar queries
- Aumentar buffer pool
- Verificar configurações do servidor

### Logs de Debug

#### Habilitar Logs Detalhados
```python
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_migracao.log'),
        logging.StreamHandler()
    ]
)

# Logger específico para MySQL
mysql_logger = logging.getLogger('mysql.connector')
mysql_logger.setLevel(logging.DEBUG)
```

## Conclusão

A migração de JSON para MySQL oferece:

### Vantagens
- **Escalabilidade:** Melhor performance com grandes volumes de dados
- **Integridade:** Transações ACID e constraints
- **Concorrência:** Múltiplos acessos simultâneos
- **Backup:** Ferramentas robustas de backup/restore
- **Monitoramento:** Métricas detalhadas de performance

### Considerações
- **Complexidade:** Maior complexidade de configuração
- **Dependências:** Requer servidor MySQL
- **Recursos:** Maior uso de recursos do sistema

### Próximos Passos
1. Monitorar performance pós-migração
2. Implementar métricas de monitoramento
3. Configurar alertas automáticos
4. Planejar estratégia de backup/restore
5. Documentar procedimentos operacionais

Para suporte adicional, consulte a documentação técnica ou entre em contato com a equipe de desenvolvimento.