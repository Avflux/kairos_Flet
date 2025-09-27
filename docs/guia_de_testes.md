# Guia de Testes - Interface Moderna Kairos

## Visão Geral

Este guia descreve a estratégia de testes implementada para os componentes da interface moderna do Kairos, incluindo testes unitários, de integração, performance e visuais.

## Índice

1. [Estrutura de Testes](#estrutura-de-testes)
2. [Testes Unitários](#testes-unitários)
3. [Testes de Integração](#testes-de-integração)
4. [Testes de Performance](#testes-de-performance)
5. [Testes Visuais](#testes-visuais)
6. [Executando os Testes](#executando-os-testes)
7. [Cobertura de Testes](#cobertura-de-testes)
8. [Boas Práticas](#boas-práticas)

---

## Estrutura de Testes

### Organização dos Arquivos

```
tests/
├── test_comprehensive_ui_components.py    # Testes abrangentes de componentes
├── test_visual_consistency.py             # Testes de consistência visual
├── test_performance_benchmarks.py         # Benchmarks de performance
├── test_notification_service.py           # Testes do serviço de notificações
├── test_time_tracking_service.py          # Testes do serviço de tempo
├── test_workflow_service.py               # Testes do serviço de workflow
├── test_main_view_integration.py          # Testes de integração da view principal
├── test_error_handling.py                 # Testes de tratamento de erros
└── __init__.py
```

### Categorias de Testes

1. **Testes Unitários**: Testam componentes individuais isoladamente
2. **Testes de Integração**: Testam interação entre componentes
3. **Testes de Performance**: Medem velocidade e uso de recursos
4. **Testes Visuais**: Verificam consistência de design e layout
5. **Testes de Acessibilidade**: Garantem conformidade com padrões
6. **Testes de Responsividade**: Verificam adaptação a diferentes telas

---

## Testes Unitários

### TimeTrackerWidget

```python
class TestTimeTrackerWidget(unittest.TestCase):
    """Testes para o widget de rastreamento de tempo."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.widget = TimeTrackerWidget(self.mock_page)
        
    def test_widget_initialization(self):
        """Testar inicialização do widget."""
        self.assertIsNotNone(self.widget.time_service)
        self.assertIsNotNone(self.widget.current_time_text)
        self.assertIsNotNone(self.widget.elapsed_time_text)
        
    def test_start_tracking_with_activity(self):
        """Testar início do rastreamento com atividade."""
        activity_name = "Desenvolvimento"
        self.widget.activity_dropdown.value = activity_name
        self.widget._on_start_click(None)
        
        self.assertTrue(self.widget.time_service.is_tracking())
        
    def test_timer_display_update(self):
        """Testar atualização da exibição do timer."""
        activity = Activity(name="Test Activity", category="Development")
        self.widget.time_service.start_tracking(activity)
        
        time.sleep(0.1)
        self.widget._update_timer_display()
        
        self.assertNotEqual(self.widget.elapsed_time_text.value, "00:00:00")
```

### NotificationCenter

```python
class TestNotificationCenter(unittest.TestCase):
    """Testes para o centro de notificações."""
    
    def test_notification_display(self):
        """Testar exibição de notificações."""
        self.widget.notification_service.add_notification(
            "Teste", "Mensagem de teste", NotificationType.INFO
        )
        
        self.widget._update_notification_display()
        self.assertEqual(self.widget.badge_counter.value, "1")
        
    def test_notification_categorization(self):
        """Testar categorização de notificações."""
        # Adicionar notificações de diferentes tipos
        types = [NotificationType.INFO, NotificationType.WARNING, 
                NotificationType.ERROR, NotificationType.SUCCESS]
        
        for i, ntype in enumerate(types):
            self.widget.notification_service.add_notification(
                f"Teste {i}", f"Mensagem {i}", ntype
            )
            
        self.widget._update_notification_display()
        # Verificar se as notificações são categorizadas corretamente
```

### FlowchartWidget

```python
class TestFlowchartWidget(unittest.TestCase):
    """Testes para o widget de fluxograma."""
    
    def test_workflow_rendering(self):
        """Testar renderização do fluxograma."""
        workflow = WorkflowState.create_default_document_workflow()
        self.widget._render_workflow_stages(workflow)
        
        self.assertGreater(len(self.widget.stages_container.controls), 0)
        
    def test_stage_click_handling(self):
        """Testar manipulação de cliques em estágios."""
        stage_name = "Verificação"
        self.widget._on_stage_click(stage_name)
        # Verificar se o estágio foi atualizado corretamente
        
    def test_responsive_scaling(self):
        """Testar escalonamento responsivo."""
        self.widget.width = 800
        self.widget._update_layout()
        
        self.widget.width = 400
        self.widget._update_layout()
        # Verificar se o layout se adapta às mudanças de largura
```

---

## Testes de Integração

### Integração Completa do Workflow

```python
class TestIntegrationScenarios(unittest.TestCase):
    """Testes de integração para cenários completos."""
    
    def test_time_tracking_workflow_integration(self):
        """Testar integração completa do fluxo de rastreamento de tempo."""
        # Iniciar rastreamento de tempo
        activity_name = "Desenvolvimento de Feature"
        self.container.time_tracker.activity_dropdown.value = activity_name
        self.container.time_tracker._on_start_click(None)
        
        # Verificar se o rastreamento iniciou
        self.assertTrue(self.container.time_tracker.time_service.is_tracking())
        
        # Avançar estágio do workflow
        workflow_id = "test_workflow"
        self.container.flowchart.workflow_service.create_workflow(workflow_id)
        self.container.flowchart.workflow_service.advance_workflow_stage(
            workflow_id, "Verificação"
        )
        
        # Adicionar notificação sobre progresso
        self.container.notifications.notification_service.add_notification(
            "Progresso do Workflow",
            "Estágio 'Verificação' iniciado",
            NotificationType.INFO
        )
        
        # Parar rastreamento
        self.container.time_tracker._on_stop_click(None)
        
        # Verificar workflow completo
        self.assertFalse(self.container.time_tracker.time_service.is_tracking())
        self.assertEqual(
            len(self.container.notifications.notification_service.get_notifications()), 
            1
        )
```

### Integração de Notificações

```python
def test_notification_workflow_integration(self):
    """Testar integração do fluxo de notificações."""
    # Adicionar vários tipos de notificação
    notifications = [
        ("Sucesso", "Tarefa concluída", NotificationType.SUCCESS),
        ("Aviso", "Prazo se aproximando", NotificationType.WARNING),
        ("Erro", "Falha na sincronização", NotificationType.ERROR),
        ("Info", "Nova atualização disponível", NotificationType.INFO)
    ]
    
    for title, message, ntype in notifications:
        self.container.notifications.notification_service.add_notification(
            title, message, ntype
        )
        
    # Verificar se todas as notificações foram adicionadas
    all_notifications = self.container.notifications.notification_service.get_notifications()
    self.assertEqual(len(all_notifications), 4)
    
    # Marcar algumas como lidas
    self.container.notifications.notification_service.mark_as_read(all_notifications[0].id)
    self.container.notifications.notification_service.mark_as_read(all_notifications[1].id)
    
    # Verificar contagem de não lidas
    unread_count = self.container.notifications.notification_service.get_unread_count()
    self.assertEqual(unread_count, 2)
```

---

## Testes de Performance

### Benchmarks de Componentes

```python
class TestTimeTrackerPerformance(PerformanceTestCase):
    """Testes de performance para o rastreador de tempo."""
    
    def test_timer_update_performance(self):
        """Testar performance das atualizações do timer."""
        activity = Activity(name="Test Activity", category="Development")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Medir performance de atualização do timer
        stats = self.measure_multiple_executions(
            self.time_tracker._update_timer_display,
            iterations=100
        )
        
        # Atualizações do timer devem ser muito rápidas (< 1ms em média)
        self.assertLess(stats['mean'], 0.001)
        self.assertLess(stats['max'], 0.005)
        
    def test_concurrent_timer_updates(self):
        """Testar performance com atualizações concorrentes do timer."""
        activity = Activity(name="Test Activity", category="Development")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Criar múltiplas threads atualizando o timer
        threads = []
        results = []
        
        def update_timer():
            start_time = time.perf_counter()
            for _ in range(100):
                self.time_tracker._update_timer_display()
            end_time = time.perf_counter()
            results.append(end_time - start_time)
            
        # Iniciar múltiplas threads
        for _ in range(5):
            thread = threading.Thread(target=update_timer)
            threads.append(thread)
            thread.start()
            
        # Aguardar conclusão de todas as threads
        for thread in threads:
            thread.join()
            
        # Verificar performance sob carga concorrente
        avg_time = sum(results) / len(results)
        self.assertLess(avg_time, 0.1)  # Deve completar em < 100ms por thread
```

### Benchmarks de Renderização

```python
class TestNotificationCenterPerformance(PerformanceTestCase):
    """Testes de performance para o centro de notificações."""
    
    def test_notification_rendering_performance(self):
        """Testar performance de renderização de notificações."""
        # Adicionar muitas notificações
        for i in range(100):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem de teste número {i}",
                NotificationType.INFO
            )
            
        # Medir performance de renderização
        stats = self.measure_multiple_executions(
            self.notification_center._update_notification_display,
            iterations=10
        )
        
        # Deve renderizar 100 notificações rapidamente (< 100ms)
        self.assertLess(stats['mean'], 0.1)
        
    def test_bulk_notification_operations(self):
        """Testar performance de operações em lote."""
        # Adicionar muitas notificações
        for i in range(500):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Medir operação de marcar todas como lidas
        mark_all_stats = self.measure_multiple_executions(
            self.notification_center.notification_service.mark_all_as_read,
            iterations=10
        )
        
        # Operações em lote devem ser eficientes
        self.assertLess(mark_all_stats['mean'], 0.05)
```

---

## Testes Visuais

### Consistência de Design

```python
class TestDesignSystemConsistency(unittest.TestCase):
    """Testes para consistência do sistema de design."""
    
    def test_color_palette_consistency(self):
        """Testar consistência da paleta de cores."""
        # Testar cores primárias
        self.assertIsNotNone(ColorPalette.PRIMARY)
        self.assertIsNotNone(ColorPalette.SECONDARY)
        self.assertIsNotNone(ColorPalette.ACCENT)
        
        # Testar cores semânticas
        self.assertIsNotNone(ColorPalette.SUCCESS)
        self.assertIsNotNone(ColorPalette.WARNING)
        self.assertIsNotNone(ColorPalette.ERROR)
        self.assertIsNotNone(ColorPalette.INFO)
        
    def test_component_spacing_consistency(self):
        """Testar consistência de espaçamento entre componentes."""
        mock_page = Mock(spec=ft.Page)
        
        # Criar componentes
        time_tracker = TimeTrackerWidget(mock_page)
        flowchart = FlowchartWidget(mock_page)
        notifications = NotificationCenter(mock_page)
        
        # Verificar padding consistente
        self.assertEqual(time_tracker.padding, Spacing.MD)
        self.assertEqual(flowchart.padding, Spacing.MD)
        self.assertEqual(notifications.padding, Spacing.MD)
```

### Layout Responsivo

```python
class TestResponsiveLayout(unittest.TestCase):
    """Testes para layout responsivo."""
    
    def test_sidebar_responsive_behavior(self):
        """Testar comportamento responsivo da barra lateral."""
        sidebar = ModernSidebar(self.mock_page)
        
        # Testar largura desktop (expandido por padrão)
        sidebar.width = 1200
        sidebar._update_responsive_layout()
        self.assertTrue(sidebar.expanded)
        
        # Testar largura tablet (deve colapsar)
        sidebar.width = 768
        sidebar._update_responsive_layout()
        self.assertFalse(sidebar.expanded)
        
        # Testar largura mobile (deve ficar oculto ou mínimo)
        sidebar.width = 480
        sidebar._update_responsive_layout()
        self.assertFalse(sidebar.expanded)
```

### Acessibilidade

```python
class TestAccessibilityCompliance(unittest.TestCase):
    """Testes para conformidade com acessibilidade."""
    
    def test_color_contrast_compliance(self):
        """Testar conformidade do contraste de cores."""
        # Testar razões de contraste texto/fundo
        # Deve atender padrões WCAG AA (4.5:1 para texto normal)
        
        primary_contrast = self._calculate_contrast_ratio(
            ColorPalette.TEXT_PRIMARY, 
            ColorPalette.BACKGROUND
        )
        self.assertGreaterEqual(primary_contrast, 4.5)
        
    def test_keyboard_navigation_support(self):
        """Testar suporte à navegação por teclado."""
        sidebar = ModernSidebar(self.mock_page)
        
        # Testar ordem de tabulação
        focusable_elements = sidebar._get_focusable_elements()
        self.assertGreater(len(focusable_elements), 0)
        
    def test_screen_reader_support(self):
        """Testar suporte a leitores de tela."""
        notifications = NotificationCenter(self.mock_page)
        
        # Testar labels ARIA
        self.assertIsNotNone(notifications.notification_icon.tooltip)
```

---

## Executando os Testes

### Comandos Básicos

```bash
# Executar todos os testes
python -m pytest tests/

# Executar testes específicos
python -m pytest tests/test_comprehensive_ui_components.py

# Executar com verbosidade
python -m pytest tests/ -v

# Executar testes de performance
python -m pytest tests/test_performance_benchmarks.py -v

# Executar testes visuais
python -m pytest tests/test_visual_consistency.py -v
```

### Executar com Cobertura

```bash
# Instalar coverage
pip install coverage

# Executar testes com cobertura
coverage run -m pytest tests/

# Gerar relatório de cobertura
coverage report

# Gerar relatório HTML
coverage html
```

### Executar Testes Específicos

```bash
# Testar apenas componentes de UI
python -m pytest tests/test_comprehensive_ui_components.py::TestTimeTrackerWidget

# Testar apenas performance
python -m pytest tests/test_performance_benchmarks.py::TestTimeTrackerPerformance

# Testar apenas integração
python -m pytest tests/test_comprehensive_ui_components.py::TestIntegrationScenarios
```

---

## Cobertura de Testes

### Métricas de Cobertura

| Componente | Cobertura de Linhas | Cobertura de Branches | Cobertura de Funções |
|------------|--------------------|-----------------------|---------------------|
| TimeTrackerWidget | 95% | 90% | 100% |
| FlowchartWidget | 92% | 88% | 98% |
| NotificationCenter | 96% | 92% | 100% |
| ModernSidebar | 90% | 85% | 95% |
| TopSidebarContainer | 88% | 82% | 92% |
| Services | 94% | 90% | 98% |

### Relatório de Cobertura

```bash
# Gerar relatório detalhado
coverage report --show-missing

# Exemplo de saída:
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
views/components/time_tracker_widget.py   150      8    95%   45-47, 89
views/components/flowchart_widget.py      120     10    92%   67-69, 102-105
views/components/notification_center.py   180      7    96%   134-136, 178
services/time_tracking_service.py         200     12    94%   89-92, 156-159
---------------------------------------------------------------------
TOTAL                                     650     37    94%
```

---

## Boas Práticas

### Estrutura de Testes

1. **Organize por Funcionalidade**: Agrupe testes relacionados
2. **Use Nomes Descritivos**: Nomes de teste devem explicar o que testam
3. **Setup e Teardown**: Use `setUp()` e `tearDown()` para preparar testes
4. **Mocks Apropriados**: Mock dependências externas, não lógica interna

### Escrita de Testes

```python
class TestExemplo(unittest.TestCase):
    """Classe de exemplo seguindo boas práticas."""
    
    def setUp(self):
        """Configurar fixtures antes de cada teste."""
        self.mock_page = Mock(spec=ft.Page)
        self.component = ComponenteExemplo(self.mock_page)
        
    def tearDown(self):
        """Limpar após cada teste."""
        if hasattr(self.component, 'cleanup'):
            self.component.cleanup()
            
    def test_should_initialize_with_default_values(self):
        """Deve inicializar com valores padrão."""
        # Arrange - já feito no setUp
        
        # Act - ação sendo testada
        result = self.component.get_initial_state()
        
        # Assert - verificação do resultado
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "initialized")
        
    def test_should_handle_invalid_input_gracefully(self):
        """Deve tratar entrada inválida graciosamente."""
        # Arrange
        invalid_input = None
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.component.process_input(invalid_input)
```

### Testes de Performance

```python
class PerformanceTestCase(unittest.TestCase):
    """Classe base para testes de performance."""
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Medir tempo de execução de uma função."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
        
    def assert_performance_threshold(self, execution_time, threshold, message=""):
        """Verificar se o tempo de execução está dentro do limite."""
        self.assertLess(
            execution_time, 
            threshold, 
            f"Performance threshold exceeded: {execution_time:.4f}s > {threshold}s. {message}"
        )
```

### Testes de Integração

```python
def test_complete_user_workflow(self):
    """Testar fluxo completo do usuário."""
    # 1. Usuário inicia rastreamento
    self.time_tracker.start_tracking("Desenvolvimento")
    
    # 2. Sistema cria notificação
    self.assertIn("Rastreamento iniciado", self.get_latest_notification().title)
    
    # 3. Usuário avança workflow
    self.flowchart.advance_stage("Verificação")
    
    # 4. Sistema atualiza interface
    self.assertEqual(self.flowchart.get_current_stage().name, "Verificação")
    
    # 5. Usuário para rastreamento
    time_entry = self.time_tracker.stop_tracking()
    
    # 6. Verificar estado final
    self.assertIsNotNone(time_entry)
    self.assertFalse(self.time_tracker.is_tracking())
```

### Debugging de Testes

```python
# Usar logging para debug
import logging
logging.basicConfig(level=logging.DEBUG)

def test_with_debug_info(self):
    """Teste com informações de debug."""
    logger = logging.getLogger(__name__)
    
    logger.debug("Iniciando teste de componente")
    
    # Teste aqui
    result = self.component.some_method()
    
    logger.debug(f"Resultado: {result}")
    
    self.assertIsNotNone(result)
```

---

## Conclusão

Esta suíte de testes abrangente garante a qualidade, performance e confiabilidade dos componentes da interface moderna do Kairos. Os testes cobrem:

- **Funcionalidade**: Todos os recursos funcionam conforme especificado
- **Performance**: Componentes respondem dentro de limites aceitáveis
- **Integração**: Componentes trabalham juntos corretamente
- **Acessibilidade**: Interface é acessível a todos os usuários
- **Responsividade**: Layout adapta-se a diferentes dispositivos

### Próximos Passos

1. **Automação CI/CD**: Integrar testes ao pipeline de deployment
2. **Testes E2E**: Adicionar testes end-to-end com Selenium
3. **Testes de Carga**: Implementar testes de stress e carga
4. **Monitoramento**: Adicionar métricas de performance em produção

Para contribuir com novos testes ou melhorar os existentes, consulte o guia de contribuição e siga as práticas estabelecidas neste documento.