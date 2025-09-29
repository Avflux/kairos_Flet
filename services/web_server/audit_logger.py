"""
Sistema de logs de auditoria para operações críticas do servidor web integrado.

Este módulo implementa um sistema robusto de auditoria que registra todas as
operações críticas do sistema, incluindo inicialização de servidor, erros,
recuperações e mudanças de configuração.
"""

import logging
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import os


class TipoEvento(Enum):
    """Tipos de eventos de auditoria."""
    
    # Eventos do servidor
    SERVIDOR_INICIADO = "SERVIDOR_INICIADO"
    SERVIDOR_PARADO = "SERVIDOR_PARADO"
    SERVIDOR_ERRO = "SERVIDOR_ERRO"
    SERVIDOR_RECUPERADO = "SERVIDOR_RECUPERADO"
    
    # Eventos do WebView
    WEBVIEW_CARREGADO = "WEBVIEW_CARREGADO"
    WEBVIEW_ERRO = "WEBVIEW_ERRO"
    WEBVIEW_FALLBACK_ATIVADO = "WEBVIEW_FALLBACK_ATIVADO"
    WEBVIEW_RECUPERADO = "WEBVIEW_RECUPERADO"
    
    # Eventos de sincronização
    SYNC_INICIADA = "SYNC_INICIADA"
    SYNC_SUCESSO = "SYNC_SUCESSO"
    SYNC_ERRO = "SYNC_ERRO"
    SYNC_RETRY = "SYNC_RETRY"
    SYNC_RECUPERADA = "SYNC_RECUPERADA"
    
    # Eventos de configuração
    CONFIG_ALTERADA = "CONFIG_ALTERADA"
    CONFIG_ERRO = "CONFIG_ERRO"
    
    # Eventos de segurança
    ACESSO_NEGADO = "ACESSO_NEGADO"
    TENTATIVA_ACESSO_SUSPEITA = "TENTATIVA_ACESSO_SUSPEITA"
    
    # Eventos de sistema
    SISTEMA_INICIADO = "SISTEMA_INICIADO"
    SISTEMA_PARADO = "SISTEMA_PARADO"
    RECURSO_INDISPONIVEL = "RECURSO_INDISPONIVEL"


class NivelSeveridade(Enum):
    """Níveis de severidade dos eventos."""
    
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class EventoAuditoria:
    """Representa um evento de auditoria."""
    
    timestamp: str
    tipo_evento: TipoEvento
    severidade: NivelSeveridade
    componente: str
    mensagem: str
    detalhes: Dict[str, Any]
    usuario: Optional[str] = None
    sessao_id: Optional[str] = None
    ip_origem: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o evento para dicionário."""
        data = asdict(self)
        data['tipo_evento'] = self.tipo_evento.value
        data['severidade'] = self.severidade.value
        return data
    
    def to_json(self) -> str:
        """Converte o evento para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AuditLogger:
    """
    Sistema de logs de auditoria para operações críticas.
    
    Registra eventos importantes do sistema com informações detalhadas
    para análise posterior e conformidade com requisitos de auditoria.
    """
    
    def __init__(
        self,
        diretorio_logs: str = "logs",
        arquivo_base: str = "auditoria",
        rotacao_diaria: bool = True,
        max_arquivos: int = 30,
        formato_timestamp: str = "%Y-%m-%d %H:%M:%S %Z",
        nivel_minimo: NivelSeveridade = NivelSeveridade.INFO,
        buffer_size: int = 100,
        flush_interval: int = 30
    ):
        """
        Inicializa o sistema de auditoria.
        
        Args:
            diretorio_logs: Diretório para armazenar logs
            arquivo_base: Nome base dos arquivos de log
            rotacao_diaria: Se deve criar um arquivo por dia
            max_arquivos: Máximo de arquivos a manter
            formato_timestamp: Formato do timestamp
            nivel_minimo: Nível mínimo de severidade para registrar
            buffer_size: Tamanho do buffer de eventos
            flush_interval: Intervalo para flush automático (segundos)
        """
        self.diretorio_logs = Path(diretorio_logs)
        self.arquivo_base = arquivo_base
        self.rotacao_diaria = rotacao_diaria
        self.max_arquivos = max_arquivos
        self.formato_timestamp = formato_timestamp
        self.nivel_minimo = nivel_minimo
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Estado interno
        self._buffer: List[EventoAuditoria] = []
        self._lock = threading.RLock()
        self._logger = self._configurar_logger()
        self._timer_flush: Optional[threading.Timer] = None
        self._ativo = True
        
        # Criar diretório se não existir
        self.diretorio_logs.mkdir(parents=True, exist_ok=True)
        
        # Iniciar flush automático
        self._iniciar_flush_automatico()
        
        # Registrar inicialização do sistema de auditoria
        self.registrar_evento(
            tipo_evento=TipoEvento.SISTEMA_INICIADO,
            severidade=NivelSeveridade.INFO,
            componente="AuditLogger",
            mensagem="Sistema de auditoria inicializado",
            detalhes={
                "diretorio_logs": str(self.diretorio_logs),
                "rotacao_diaria": self.rotacao_diaria,
                "nivel_minimo": self.nivel_minimo.value,
                "buffer_size": self.buffer_size
            }
        )
    
    def _configurar_logger(self) -> logging.Logger:
        """Configura o logger interno."""
        logger = logging.getLogger(f"{__name__}.AuditLogger")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - [AUDIT] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _obter_nome_arquivo(self) -> str:
        """Obtém o nome do arquivo de log atual."""
        if self.rotacao_diaria:
            data_atual = datetime.now().strftime("%Y-%m-%d")
            return f"{self.arquivo_base}_{data_atual}.json"
        else:
            return f"{self.arquivo_base}.json"
    
    def _obter_caminho_arquivo(self) -> Path:
        """Obtém o caminho completo do arquivo de log atual."""
        return self.diretorio_logs / self._obter_nome_arquivo()
    
    def _iniciar_flush_automatico(self) -> None:
        """Inicia o timer para flush automático."""
        if self._timer_flush:
            self._timer_flush.cancel()
        
        self._timer_flush = threading.Timer(self.flush_interval, self._flush_automatico)
        self._timer_flush.daemon = True
        self._timer_flush.start()
    
    def _flush_automatico(self) -> None:
        """Executa flush automático do buffer."""
        try:
            self.flush()
        except Exception as e:
            self._logger.error(f"Erro no flush automático: {e}")
        finally:
            if self._ativo:
                self._iniciar_flush_automatico()
    
    def registrar_evento(
        self,
        tipo_evento: TipoEvento,
        severidade: NivelSeveridade,
        componente: str,
        mensagem: str,
        detalhes: Optional[Dict[str, Any]] = None,
        usuario: Optional[str] = None,
        sessao_id: Optional[str] = None,
        ip_origem: Optional[str] = None
    ) -> None:
        """
        Registra um evento de auditoria.
        
        Args:
            tipo_evento: Tipo do evento
            severidade: Nível de severidade
            componente: Componente que gerou o evento
            mensagem: Mensagem descritiva
            detalhes: Detalhes adicionais do evento
            usuario: Usuário associado ao evento
            sessao_id: ID da sessão
            ip_origem: IP de origem da requisição
        """
        # Verificar se deve registrar baseado no nível mínimo
        if self._deve_ignorar_severidade(severidade):
            return
        
        # Criar evento
        evento = EventoAuditoria(
            timestamp=datetime.now(timezone.utc).strftime(self.formato_timestamp),
            tipo_evento=tipo_evento,
            severidade=severidade,
            componente=componente,
            mensagem=mensagem,
            detalhes=detalhes or {},
            usuario=usuario,
            sessao_id=sessao_id,
            ip_origem=ip_origem
        )
        
        with self._lock:
            # Adicionar ao buffer
            self._buffer.append(evento)
            
            # Log no console se for crítico
            if severidade == NivelSeveridade.CRITICAL:
                self._logger.critical(f"[{componente}] {mensagem}")
            elif severidade == NivelSeveridade.ERROR:
                self._logger.error(f"[{componente}] {mensagem}")
            elif severidade == NivelSeveridade.WARNING:
                self._logger.warning(f"[{componente}] {mensagem}")
            
            # Flush se buffer estiver cheio ou for evento crítico
            if (len(self._buffer) >= self.buffer_size or 
                severidade == NivelSeveridade.CRITICAL):
                self._flush_buffer()
    
    def _deve_ignorar_severidade(self, severidade: NivelSeveridade) -> bool:
        """Verifica se deve ignorar evento baseado na severidade."""
        ordem_severidade = {
            NivelSeveridade.INFO: 0,
            NivelSeveridade.WARNING: 1,
            NivelSeveridade.ERROR: 2,
            NivelSeveridade.CRITICAL: 3
        }
        
        return ordem_severidade[severidade] < ordem_severidade[self.nivel_minimo]
    
    def _flush_buffer(self) -> None:
        """Escreve o buffer no arquivo de log."""
        if not self._buffer:
            return
        
        try:
            caminho_arquivo = self._obter_caminho_arquivo()
            
            # Ler eventos existentes se arquivo já existe
            eventos_existentes = []
            if caminho_arquivo.exists():
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read().strip()
                        if conteudo:
                            eventos_existentes = json.loads(conteudo)
                except (json.JSONDecodeError, IOError) as e:
                    self._logger.warning(f"Erro ao ler arquivo existente: {e}")
            
            # Adicionar novos eventos
            novos_eventos = [evento.to_dict() for evento in self._buffer]
            todos_eventos = eventos_existentes + novos_eventos
            
            # Escrever arquivo atualizado
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(todos_eventos, f, ensure_ascii=False, indent=2)
            
            # Limpar buffer
            self._buffer.clear()
            
            # Limpar arquivos antigos se necessário
            self._limpar_arquivos_antigos()
            
        except Exception as e:
            self._logger.error(f"Erro ao escrever log de auditoria: {e}")
    
    def _limpar_arquivos_antigos(self) -> None:
        """Remove arquivos de log antigos baseado no limite configurado."""
        try:
            # Listar arquivos de log
            pattern = f"{self.arquivo_base}_*.json" if self.rotacao_diaria else f"{self.arquivo_base}.json"
            arquivos_log = list(self.diretorio_logs.glob(pattern))
            
            # Ordenar por data de modificação (mais recente primeiro)
            arquivos_log.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remover arquivos excedentes
            for arquivo in arquivos_log[self.max_arquivos:]:
                try:
                    arquivo.unlink()
                    self._logger.info(f"Arquivo de log antigo removido: {arquivo}")
                except OSError as e:
                    self._logger.warning(f"Erro ao remover arquivo antigo {arquivo}: {e}")
                    
        except Exception as e:
            self._logger.error(f"Erro ao limpar arquivos antigos: {e}")
    
    def flush(self) -> None:
        """Força a escrita do buffer no arquivo."""
        with self._lock:
            self._flush_buffer()
    
    def obter_eventos(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        tipo_evento: Optional[TipoEvento] = None,
        severidade: Optional[NivelSeveridade] = None,
        componente: Optional[str] = None,
        limite: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém eventos de auditoria com filtros.
        
        Args:
            data_inicio: Data de início do filtro
            data_fim: Data de fim do filtro
            tipo_evento: Filtrar por tipo de evento
            severidade: Filtrar por severidade
            componente: Filtrar por componente
            limite: Limite de eventos a retornar
            
        Returns:
            Lista de eventos filtrados
        """
        eventos = []
        
        try:
            # Listar arquivos de log relevantes
            if self.rotacao_diaria and (data_inicio or data_fim):
                arquivos_relevantes = self._obter_arquivos_por_periodo(data_inicio, data_fim)
            else:
                arquivos_relevantes = list(self.diretorio_logs.glob(f"{self.arquivo_base}*.json"))
            
            # Ler eventos de todos os arquivos relevantes
            for arquivo in arquivos_relevantes:
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        eventos_arquivo = json.load(f)
                        eventos.extend(eventos_arquivo)
                except (json.JSONDecodeError, IOError) as e:
                    self._logger.warning(f"Erro ao ler arquivo {arquivo}: {e}")
            
            # Aplicar filtros
            eventos_filtrados = self._aplicar_filtros(
                eventos, data_inicio, data_fim, tipo_evento, severidade, componente
            )
            
            # Ordenar por timestamp (mais recente primeiro)
            eventos_filtrados.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Aplicar limite
            if limite:
                eventos_filtrados = eventos_filtrados[:limite]
            
            return eventos_filtrados
            
        except Exception as e:
            self._logger.error(f"Erro ao obter eventos: {e}")
            return []
    
    def _obter_arquivos_por_periodo(
        self, 
        data_inicio: Optional[datetime], 
        data_fim: Optional[datetime]
    ) -> List[Path]:
        """Obtém arquivos de log relevantes para um período."""
        arquivos = []
        
        # Se não há filtro de data, retornar todos
        if not data_inicio and not data_fim:
            return list(self.diretorio_logs.glob(f"{self.arquivo_base}_*.json"))
        
        # Gerar lista de datas no período
        inicio = data_inicio or datetime.now().replace(day=1)  # Início do mês se não especificado
        fim = data_fim or datetime.now()
        
        data_atual = inicio
        while data_atual <= fim:
            nome_arquivo = f"{self.arquivo_base}_{data_atual.strftime('%Y-%m-%d')}.json"
            caminho_arquivo = self.diretorio_logs / nome_arquivo
            
            if caminho_arquivo.exists():
                arquivos.append(caminho_arquivo)
            
            data_atual = data_atual.replace(day=data_atual.day + 1)
        
        return arquivos
    
    def _aplicar_filtros(
        self,
        eventos: List[Dict[str, Any]],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime],
        tipo_evento: Optional[TipoEvento],
        severidade: Optional[NivelSeveridade],
        componente: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Aplica filtros aos eventos."""
        eventos_filtrados = eventos
        
        # Filtro por data
        if data_inicio or data_fim:
            eventos_filtrados = [
                evento for evento in eventos_filtrados
                if self._evento_no_periodo(evento, data_inicio, data_fim)
            ]
        
        # Filtro por tipo de evento
        if tipo_evento:
            eventos_filtrados = [
                evento for evento in eventos_filtrados
                if evento.get('tipo_evento') == tipo_evento.value
            ]
        
        # Filtro por severidade
        if severidade:
            eventos_filtrados = [
                evento for evento in eventos_filtrados
                if evento.get('severidade') == severidade.value
            ]
        
        # Filtro por componente
        if componente:
            eventos_filtrados = [
                evento for evento in eventos_filtrados
                if componente.lower() in evento.get('componente', '').lower()
            ]
        
        return eventos_filtrados
    
    def _evento_no_periodo(
        self, 
        evento: Dict[str, Any], 
        data_inicio: Optional[datetime], 
        data_fim: Optional[datetime]
    ) -> bool:
        """Verifica se evento está no período especificado."""
        try:
            timestamp_str = evento.get('timestamp', '')
            timestamp = datetime.fromisoformat(timestamp_str.replace(' UTC', '+00:00'))
            
            if data_inicio and timestamp < data_inicio:
                return False
            
            if data_fim and timestamp > data_fim:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return True  # Incluir eventos com timestamp inválido
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas dos logs de auditoria."""
        try:
            eventos = self.obter_eventos()
            
            # Contar por tipo de evento
            contadores_tipo = {}
            for evento in eventos:
                tipo = evento.get('tipo_evento', 'DESCONHECIDO')
                contadores_tipo[tipo] = contadores_tipo.get(tipo, 0) + 1
            
            # Contar por severidade
            contadores_severidade = {}
            for evento in eventos:
                sev = evento.get('severidade', 'DESCONHECIDO')
                contadores_severidade[sev] = contadores_severidade.get(sev, 0) + 1
            
            # Contar por componente
            contadores_componente = {}
            for evento in eventos:
                comp = evento.get('componente', 'DESCONHECIDO')
                contadores_componente[comp] = contadores_componente.get(comp, 0) + 1
            
            return {
                "total_eventos": len(eventos),
                "eventos_no_buffer": len(self._buffer),
                "por_tipo": contadores_tipo,
                "por_severidade": contadores_severidade,
                "por_componente": contadores_componente,
                "arquivos_log": len(list(self.diretorio_logs.glob(f"{self.arquivo_base}*.json"))),
                "diretorio_logs": str(self.diretorio_logs),
                "ultimo_flush": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"Erro ao obter estatísticas: {e}")
            return {"erro": str(e)}
    
    def finalizar(self) -> None:
        """Finaliza o sistema de auditoria."""
        self._ativo = False
        
        # Cancelar timer
        if self._timer_flush:
            self._timer_flush.cancel()
        
        # Flush final
        self.flush()
        
        # Registrar finalização
        self.registrar_evento(
            tipo_evento=TipoEvento.SISTEMA_PARADO,
            severidade=NivelSeveridade.INFO,
            componente="AuditLogger",
            mensagem="Sistema de auditoria finalizado",
            detalhes={"eventos_processados": len(self._buffer)}
        )
        
        # Flush final após registro de finalização
        self.flush()
    
    def __enter__(self):
        """Suporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte para context manager."""
        self.finalizar()


# Instância global do audit logger (singleton)
_audit_logger_instance: Optional[AuditLogger] = None
_audit_logger_lock = threading.Lock()


def obter_audit_logger(**kwargs) -> AuditLogger:
    """
    Obtém a instância global do audit logger (singleton).
    
    Args:
        **kwargs: Argumentos para inicialização (apenas na primeira chamada)
        
    Returns:
        Instância do AuditLogger
    """
    global _audit_logger_instance
    
    with _audit_logger_lock:
        if _audit_logger_instance is None:
            _audit_logger_instance = AuditLogger(**kwargs)
        
        return _audit_logger_instance


def registrar_evento_auditoria(
    tipo_evento: TipoEvento,
    severidade: NivelSeveridade,
    componente: str,
    mensagem: str,
    detalhes: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Função de conveniência para registrar eventos de auditoria.
    
    Args:
        tipo_evento: Tipo do evento
        severidade: Nível de severidade
        componente: Componente que gerou o evento
        mensagem: Mensagem descritiva
        detalhes: Detalhes adicionais do evento
        **kwargs: Argumentos adicionais para o evento
    """
    audit_logger = obter_audit_logger()
    audit_logger.registrar_evento(
        tipo_evento=tipo_evento,
        severidade=severidade,
        componente=componente,
        mensagem=mensagem,
        detalhes=detalhes,
        **kwargs
    )