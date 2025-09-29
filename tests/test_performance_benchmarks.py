"""
Testes de performance e benchmarks para componentes da UI moderna.
Performance tests and benchmarks for modern UI components.
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import statistics
import gc

# Import components for performance testing
from views.components.time_tracker_widget import TimeTrackerWidget
from views.components.flowchart_widget import FlowchartWidget
from views.components.notification_center import NotificationCenter
from views.components.modern_sidebar import ModernSidebar
from views.components.top_sidebar_container import TopSidebarContainer

# Import services
from services.time_tracking_service import TimeTrackingService
from services.notification_service import NotificationService
from services.workflow_service import WorkflowService

# Import models
from models.activity import Activity
from models.notification import Notification, NotificationType
from models.time_entry import TimeEntry


class PerformanceTestCase(unittest.TestCase):
    """Classe base para testes de performance."""
    
    def setUp(self):
        """Configurar fixtures de teste."""
        self.mock_page = Mock()
        self.mock_page.update = Mock()
        
    def measure_execution_time(self, func, *args, **kwargs):
        """Medir tempo de execução de uma função."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
        
    def measure_multiple_executions(self, func, iterations=10, *args, **kwargs):
        """Medir múltiplas execuções e retornar estatísticas."""
        times = []
        for _ in range(iterations):
            _, execution_time = self.measure_execution_time(func, *args, **kwargs)
            times.append(execution_time)
            
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }


class TestTimeTrackerPerformance(PerformanceTestCase):
    """Testes de performance para o rastreador de tempo."""
    
    def setUp(self):
        super().setUp()
        self.time_tracker = TimeTrackerWidget(self.mock_page)
        
    def test_timer_update_performance(self):
        """Testar performance das atualizações do timer."""
        # Start tracking
        activity = Activity(name="Test Activity", category="Development")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Measure timer update performance
        stats = self.measure_multiple_executions(
            self.time_tracker._update_timer_display,
            iterations=100
        )
        
        # Timer updates should be very fast (< 1ms average)
        self.assertLess(stats['mean'], 0.001)
        self.assertLess(stats['max'], 0.005)
        
    def test_start_stop_tracking_performance(self):
        """Testar performance de iniciar/parar rastreamento."""
        activity = Activity(name="Test Activity", category="Development")
        
        # Measure start tracking performance
        start_stats = self.measure_multiple_executions(
            self.time_tracker.time_service.start_tracking,
            iterations=50,
            activity=activity
        )
        
        # Stop tracking for each iteration
        for _ in range(50):
            self.time_tracker.time_service.stop_tracking()
            
        # Start/stop should be fast (< 10ms)
        self.assertLess(start_stats['mean'], 0.01)
        
    def test_elapsed_time_calculation_performance(self):
        """Testar performance do cálculo de tempo decorrido."""
        activity = Activity(name="Test Activity", category="Development")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Let some time pass
        time.sleep(0.01)
        
        # Measure elapsed time calculation
        stats = self.measure_multiple_executions(
            self.time_tracker.time_service.get_elapsed_time,
            iterations=1000
        )
        
        # Elapsed time calculation should be very fast
        self.assertLess(stats['mean'], 0.0001)
        
    def test_concurrent_timer_updates(self):
        """Testar performance com atualizações concorrentes do timer."""
        activity = Activity(name="Test Activity", category="Development")
        self.time_tracker.time_service.start_tracking(activity)
        
        # Create multiple threads updating timer
        threads = []
        results = []
        
        def update_timer():
            start_time = time.perf_counter()
            for _ in range(100):
                self.time_tracker._update_timer_display()
            end_time = time.perf_counter()
            results.append(end_time - start_time)
            
        # Start multiple threads
        for _ in range(5):
            thread = threading.Thread(target=update_timer)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Verify performance under concurrent load
        avg_time = sum(results) / len(results)
        self.assertLess(avg_time, 0.1)  # Should complete within 100ms per thread
        
    def test_memory_usage_during_long_tracking(self):
        """Testar uso de memória durante rastreamento longo."""
        activity = Activity(name="Test Activity", category="Development")
        
        # Force garbage collection before test
        gc.collect()
        
        # Start tracking
        self.time_tracker.time_service.start_tracking(activity)
        
        # Simulate long tracking session with frequent updates
        for _ in range(1000):
            self.time_tracker._update_timer_display()
            if _ % 100 == 0:
                # Periodic garbage collection check
                gc.collect()
                
        # Stop tracking
        self.time_tracker.time_service.stop_tracking()
        
        # Memory should be stable (no significant leaks)
        # This would require actual memory measurement in practice


class TestNotificationCenterPerformance(PerformanceTestCase):
    """Testes de performance para o centro de notificações."""
    
    def setUp(self):
        super().setUp()
        self.notification_center = NotificationCenter(self.mock_page)
        
    def test_notification_rendering_performance(self):
        """Testar performance de renderização de notificações."""
        # Add many notifications
        for i in range(100):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem de teste número {i}",
                NotificationType.INFO
            )
            
        # Measure rendering performance
        stats = self.measure_multiple_executions(
            self.notification_center._update_notification_display,
            iterations=10
        )
        
        # Should render 100 notifications quickly (< 100ms)
        self.assertLess(stats['mean'], 0.1)
        
    def test_notification_filtering_performance(self):
        """Testar performance de filtragem de notificações."""
        # Add notifications of different types
        for i in range(1000):
            notification_type = [
                NotificationType.INFO,
                NotificationType.WARNING,
                NotificationType.ERROR,
                NotificationType.SUCCESS
            ][i % 4]
            
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                notification_type
            )
            
        # Measure filtering performance
        stats = self.measure_multiple_executions(
            self.notification_center.notification_service.get_notifications,
            iterations=50,
            notification_type=NotificationType.ERROR
        )
        
        # Filtering should be fast even with many notifications
        self.assertLess(stats['mean'], 0.01)
        
    def test_bulk_notification_operations(self):
        """Testar performance de operações em lote."""
        # Add many notifications
        for i in range(500):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Measure bulk mark as read
        mark_all_stats = self.measure_multiple_executions(
            self.notification_center.notification_service.mark_all_as_read,
            iterations=10
        )
        
        # Measure bulk clear
        clear_all_stats = self.measure_multiple_executions(
            self.notification_center.notification_service.clear_all_notifications,
            iterations=10
        )
        
        # Bulk operations should be efficient
        self.assertLess(mark_all_stats['mean'], 0.05)
        self.assertLess(clear_all_stats['mean'], 0.05)
        
    def test_notification_panel_toggle_performance(self):
        """Testar performance de alternância do painel."""
        # Add some notifications
        for i in range(50):
            self.notification_center.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Measure panel toggle performance
        stats = self.measure_multiple_executions(
            self.notification_center._toggle_notification_panel,
            iterations=20,
            event=None
        )
        
        # Panel toggle should be smooth
        self.assertLess(stats['mean'], 0.01)


class TestFlowchartWidgetPerformance(PerformanceTestCase):
    """Testes de performance para o widget de fluxograma."""
    
    def setUp(self):
        super().setUp()
        self.flowchart = FlowchartWidget(self.mock_page)
        
    def test_workflow_rendering_performance(self):
        """Testar performance de renderização do fluxograma."""
        # Create workflow with many stages
        from models.workflow_state import WorkflowState
        workflow = WorkflowState.create_default_document_workflow()
        
        # Measure rendering performance
        stats = self.measure_multiple_executions(
            self.flowchart._render_workflow_stages,
            iterations=20,
            workflow=workflow
        )
        
        # Workflow rendering should be fast
        self.assertLess(stats['mean'], 0.05)
        
    def test_stage_interaction_performance(self):
        """Testar performance de interação com estágios."""
        # Setup workflow
        workflow_id = "test_workflow"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Measure stage click performance
        stats = self.measure_multiple_executions(
            self.flowchart._on_stage_click,
            iterations=50,
            stage_name="Verificação"
        )
        
        # Stage interactions should be responsive
        self.assertLess(stats['mean'], 0.01)
        
    def test_workflow_update_performance(self):
        """Testar performance de atualização do fluxograma."""
        workflow_id = "test_workflow"
        self.flowchart.workflow_service.create_workflow(workflow_id)
        
        # Measure workflow update performance
        stats = self.measure_multiple_executions(
            self.flowchart._update_workflow_display,
            iterations=30
        )
        
        # Workflow updates should be efficient
        self.assertLess(stats['mean'], 0.02)
        
    def test_responsive_layout_performance(self):
        """Testar performance do layout responsivo."""
        # Test different container widths
        widths = [400, 600, 800, 1000, 1200]
        
        for width in widths:
            self.flowchart.width = width
            
            # Measure layout update performance
            _, execution_time = self.measure_execution_time(
                self.flowchart._update_stage_layout
            )
            
            # Layout updates should be fast regardless of width
            self.assertLess(execution_time, 0.01)


class TestModernSidebarPerformance(PerformanceTestCase):
    """Testes de performance para a barra lateral moderna."""
    
    def setUp(self):
        super().setUp()
        self.sidebar = ModernSidebar(self.mock_page)
        
    def test_sidebar_expansion_performance(self):
        """Testar performance de expansão/colapso da barra lateral."""
        # Measure expansion performance
        expand_stats = self.measure_multiple_executions(
            self.sidebar.toggle_expansion,
            iterations=20
        )
        
        # Expansion should be smooth
        self.assertLess(expand_stats['mean'], 0.01)
        
    def test_navigation_item_creation_performance(self):
        """Testar performance de criação de itens de navegação."""
        # Measure navigation item creation
        stats = self.measure_multiple_executions(
            self.sidebar._create_nav_item,
            iterations=100,
            text="Item de Teste",
            icon="test_icon"
        )
        
        # Item creation should be fast
        self.assertLess(stats['mean'], 0.001)
        
    def test_section_update_performance(self):
        """Testar performance de atualização de seções."""
        # Measure section update performance
        stats = self.measure_multiple_executions(
            self.sidebar.update_active_section,
            iterations=50,
            section_name="Gerenciamento de Tempo"
        )
        
        # Section updates should be responsive
        self.assertLess(stats['mean'], 0.005)
        
    def test_hover_effect_performance(self):
        """Testar performance dos efeitos de hover."""
        nav_item = self.sidebar._create_nav_item("Teste", "test_icon")
        
        # Measure hover effect performance
        hover_in_stats = self.measure_multiple_executions(
            nav_item._on_hover_in,
            iterations=50
        )
        
        hover_out_stats = self.measure_multiple_executions(
            nav_item._on_hover_out,
            iterations=50
        )
        
        # Hover effects should be smooth
        self.assertLess(hover_in_stats['mean'], 0.001)
        self.assertLess(hover_out_stats['mean'], 0.001)


class TestTopSidebarContainerPerformance(PerformanceTestCase):
    """Testes de performance para o contêiner da barra lateral superior."""
    
    def setUp(self):
        super().setUp()
        self.container = TopSidebarContainer(self.mock_page)
        
    def test_layout_update_performance(self):
        """Testar performance de atualização do layout."""
        # Measure layout update performance for different states
        expanded_stats = self.measure_multiple_executions(
            self.container.update_layout,
            iterations=30,
            sidebar_expanded=True
        )
        
        collapsed_stats = self.measure_multiple_executions(
            self.container.update_layout,
            iterations=30,
            sidebar_expanded=False
        )
        
        # Layout updates should be fast
        self.assertLess(expanded_stats['mean'], 0.01)
        self.assertLess(collapsed_stats['mean'], 0.01)
        
    def test_component_refresh_performance(self):
        """Testar performance de atualização dos componentes."""
        # Measure component refresh performance
        stats = self.measure_multiple_executions(
            self.container.refresh_components,
            iterations=20
        )
        
        # Component refresh should be efficient
        self.assertLess(stats['mean'], 0.02)
        
    def test_responsive_adaptation_performance(self):
        """Testar performance de adaptação responsiva."""
        # Test different screen sizes
        screen_sizes = [
            (1920, 1080),
            (1366, 768),
            (1024, 768),
            (768, 1024),
            (375, 667)
        ]
        
        for width, height in screen_sizes:
            self.container.width = width
            self.container.height = height
            
            # Measure adaptation performance
            _, execution_time = self.measure_execution_time(
                self.container._adapt_to_screen_size
            )
            
            # Adaptation should be fast for all screen sizes
            self.assertLess(execution_time, 0.005)


class TestIntegratedPerformance(PerformanceTestCase):
    """Testes de performance integrada para todos os componentes."""
    
    def setUp(self):
        super().setUp()
        self.container = TopSidebarContainer(self.mock_page)
        self.sidebar = ModernSidebar(self.mock_page)
        
    def test_full_ui_initialization_performance(self):
        """Testar performance de inicialização completa da UI."""
        # Measure full UI initialization
        def initialize_full_ui():
            container = TopSidebarContainer(self.mock_page)
            sidebar = ModernSidebar(self.mock_page)
            return container, sidebar
            
        stats = self.measure_multiple_executions(
            initialize_full_ui,
            iterations=10
        )
        
        # Full UI initialization should be reasonable (< 100ms)
        self.assertLess(stats['mean'], 0.1)
        
    def test_concurrent_component_updates(self):
        """Testar performance com atualizações concorrentes."""
        # Start time tracking
        activity = Activity(name="Test Activity", category="Development")
        self.container.time_tracker.time_service.start_tracking(activity)
        
        # Add notifications
        for i in range(10):
            self.container.notifications.notification_service.add_notification(
                f"Notificação {i}",
                f"Mensagem {i}",
                NotificationType.INFO
            )
            
        # Measure concurrent updates
        def concurrent_updates():
            # Update timer
            self.container.time_tracker._update_timer_display()
            # Update notifications
            self.container.notifications._update_notification_display()
            # Update flowchart
            self.container.flowchart._update_workflow_display()
            # Update sidebar
            self.sidebar._update_layout()
            
        stats = self.measure_multiple_executions(
            concurrent_updates,
            iterations=50
        )
        
        # Concurrent updates should be efficient
        self.assertLess(stats['mean'], 0.02)
        
    def test_memory_stability_under_load(self):
        """Testar estabilidade de memória sob carga."""
        # Simulate heavy usage
        for cycle in range(10):
            # Add many notifications
            for i in range(50):
                self.container.notifications.notification_service.add_notification(
                    f"Ciclo {cycle} - Notificação {i}",
                    f"Mensagem {i}",
                    NotificationType.INFO
                )
                
            # Update displays multiple times
            for _ in range(20):
                self.container.notifications._update_notification_display()
                self.container.flowchart._update_workflow_display()
                
            # Clear notifications
            self.container.notifications.notification_service.clear_all_notifications()
            
            # Force garbage collection
            gc.collect()
            
        # Memory should be stable after cleanup
        # This would require actual memory measurement in practice
        
    def test_ui_responsiveness_under_load(self):
        """Testar responsividade da UI sob carga."""
        # Create heavy load scenario
        
        # Start multiple time tracking sessions
        activities = [
            Activity(name=f"Atividade {i}", category="Development")
            for i in range(5)
        ]
        
        # Add many notifications
        for i in range(200):
            self.container.notifications.notification_service.add_notification(
                f"Notificação de Carga {i}",
                f"Mensagem de teste sob carga {i}",
                NotificationType.INFO
            )
            
        # Measure UI update performance under load
        def ui_update_under_load():
            self.container.refresh_components()
            self.sidebar._update_layout()
            
        stats = self.measure_multiple_executions(
            ui_update_under_load,
            iterations=20
        )
        
        # UI should remain responsive even under load
        self.assertLess(stats['mean'], 0.05)
        self.assertLess(stats['max'], 0.1)


if __name__ == '__main__':
    # Run performance tests with detailed output
    unittest.main(verbosity=2)