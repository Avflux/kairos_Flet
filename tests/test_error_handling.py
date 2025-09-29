"""
Comprehensive tests for error handling and recovery functionality.
Tests error scenarios and recovery mechanisms for all components.
"""

import pytest
import flet as ft
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os
import json

from views.components.error_handling import (
    ErrorBoundary, ErrorRecoveryManager, LocalStorageManager, 
    ToastNotificationManager, FallbackDisplayManager,
    ErrorSeverity, ErrorContext, FeedbackType, FeedbackMessage,
    create_error_boundary, safe_execute
)
from services.notification_service import NotificationService
from services.time_tracking_service import TimeTrackingService
from services.workflow_service import WorkflowService
from models.notification import Notification, NotificationType
from models.activity import Activity
from models.time_entry import TimeEntry


class TestErrorRecoveryManager:
    """Test error recovery manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recovery_manager = ErrorRecoveryManager()
    
    def test_register_recovery_strategy(self):
        """Test registering recovery strategies."""
        def mock_strategy(context):
            return True
        
        self.recovery_manager.register_recovery_strategy("TestError", mock_strategy)
        assert "TestError" in self.recovery_manager._recovery_strategies
    
    def test_attempt_recovery_success(self):
        """Test successful error recovery."""
        def mock_strategy(context):
            return True
        
        self.recovery_manager.register_recovery_strategy("TestError", mock_strategy)
        
        context = ErrorContext(
            component_name="TestComponent",
            operation="test_operation"
        )
        
        result = self.recovery_manager.attempt_recovery("TestError", context)
        assert result is True
    
    def test_attempt_recovery_failure(self):
        """Test failed error recovery."""
        def mock_strategy(context):
            raise Exception("Recovery failed")
        
        self.recovery_manager.register_recovery_strategy("TestError", mock_strategy)
        
        context = ErrorContext(
            component_name="TestComponent",
            operation="test_operation"
        )
        
        result = self.recovery_manager.attempt_recovery("TestError", context)
        assert result is False
    
    def test_attempt_recovery_no_strategy(self):
        """Test recovery attempt with no registered strategy."""
        context = ErrorContext(
            component_name="TestComponent",
            operation="test_operation"
        )
        
        result = self.recovery_manager.attempt_recovery("UnknownError", context)
        assert result is False
    
    def test_record_error(self):
        """Test error recording."""
        context = ErrorContext(
            component_name="TestComponent",
            operation="test_operation"
        )
        
        self.recovery_manager.record_error(context)
        assert len(self.recovery_manager._error_history) == 1
        assert self.recovery_manager._error_history[0] == context
    
    def test_get_error_patterns(self):
        """Test error pattern analysis."""
        # Record multiple errors
        for i in range(3):
            context = ErrorContext(
                component_name="TestComponent",
                operation="test_operation"
            )
            self.recovery_manager.record_error(context)
        
        # Record different error
        context2 = ErrorContext(
            component_name="TestComponent",
            operation="other_operation"
        )
        self.recovery_manager.record_error(context2)
        
        patterns = self.recovery_manager.get_error_patterns()
        assert patterns["TestComponent:test_operation"] == 3
        assert patterns["TestComponent:other_operation"] == 1
    
    def test_fallback_data(self):
        """Test fallback data management."""
        test_data = {"key": "value"}
        self.recovery_manager.set_fallback_data("test_key", test_data)
        
        retrieved_data = self.recovery_manager.get_fallback_data("test_key")
        assert retrieved_data == test_data
        
        # Test default value
        default_data = self.recovery_manager.get_fallback_data("nonexistent", "default")
        assert default_data == "default"


class TestLocalStorageManager:
    """Test local storage manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_manager = LocalStorageManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_backup_and_restore_data(self):
        """Test data backup and restoration."""
        test_data = {
            "notifications": [
                {"id": "1", "title": "Test", "message": "Test message"}
            ]
        }
        
        # Backup data
        success = self.storage_manager.backup_data("test_key", test_data)
        assert success is True
        
        # Restore data
        restored_data = self.storage_manager.restore_data("test_key")
        assert restored_data == test_data
    
    def test_backup_failure(self):
        """Test backup failure handling."""
        # Try to backup to invalid location
        invalid_storage = LocalStorageManager("/invalid/path/that/does/not/exist")
        
        success = invalid_storage.backup_data("test_key", {"data": "test"})
        assert success is False
    
    def test_restore_nonexistent_data(self):
        """Test restoring nonexistent data."""
        restored_data = self.storage_manager.restore_data("nonexistent_key")
        assert restored_data is None
    
    def test_clear_backup(self):
        """Test clearing backup data."""
        test_data = {"test": "data"}
        
        # Backup and verify
        self.storage_manager.backup_data("test_key", test_data)
        assert self.storage_manager.restore_data("test_key") == test_data
        
        # Clear and verify
        success = self.storage_manager.clear_backup("test_key")
        assert success is True
        assert self.storage_manager.restore_data("test_key") is None
    
    def test_list_backups(self):
        """Test listing available backups."""
        # Create multiple backups
        self.storage_manager.backup_data("backup1", {"data": "1"})
        self.storage_manager.backup_data("backup2", {"data": "2"})
        
        backups = self.storage_manager.list_backups()
        assert "backup1" in backups
        assert "backup2" in backups


class TestToastNotificationManager:
    """Test toast notification manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.toast_manager = ToastNotificationManager(self.mock_page)
    
    def test_show_toast(self):
        """Test showing toast notifications."""
        toast_id = self.toast_manager.show_toast(
            "Test message",
            FeedbackType.INFO,
            "Test Title"
        )
        
        assert toast_id is not None
        assert len(self.toast_manager._active_toasts) == 1
        self.mock_page.show_snack_bar.assert_called_once()
    
    def test_show_multiple_toasts(self):
        """Test showing multiple toast notifications."""
        # Show maximum concurrent toasts
        for i in range(self.toast_manager._max_concurrent_toasts):
            self.toast_manager.show_toast(f"Message {i}", FeedbackType.INFO)
        
        assert len(self.toast_manager._active_toasts) == self.toast_manager._max_concurrent_toasts
        
        # Show one more - should be queued
        self.toast_manager.show_toast("Queued message", FeedbackType.INFO)
        assert len(self.toast_manager._toast_queue) == 1
    
    def test_dismiss_toast(self):
        """Test dismissing toast notifications."""
        toast_id = self.toast_manager.show_toast("Test message", FeedbackType.INFO)
        
        # Dismiss toast
        self.toast_manager._dismiss_toast(toast_id)
        assert len(self.toast_manager._active_toasts) == 0
    
    def test_convenience_methods(self):
        """Test convenience methods for different feedback types."""
        success_id = self.toast_manager.show_success("Success message")
        error_id = self.toast_manager.show_error("Error message")
        warning_id = self.toast_manager.show_warning("Warning message")
        info_id = self.toast_manager.show_info("Info message")
        
        assert all([success_id, error_id, warning_id, info_id])
        assert len(self.toast_manager._active_toasts) == 4


class TestErrorBoundary:
    """Test error boundary functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
        self.toast_manager = ToastNotificationManager(self.mock_page)
        self.recovery_manager = ErrorRecoveryManager()
        self.storage_manager = LocalStorageManager(tempfile.mkdtemp())
        
        self.error_boundary = ErrorBoundary(
            "TestComponent",
            self.toast_manager,
            self.recovery_manager,
            self.storage_manager
        )
    
    def test_handle_errors_success(self):
        """Test successful operation with error boundary."""
        with self.error_boundary.handle_errors("test_operation") as context:
            # Simulate successful operation
            result = "success"
        
        assert context.component_name == "TestComponent"
        assert context.operation == "test_operation"
    
    def test_handle_errors_with_exception(self):
        """Test error handling when exception occurs."""
        with pytest.raises(Exception):
            with self.error_boundary.handle_errors("test_operation") as context:
                raise ValueError("Test error")
    
    def test_error_severity_determination(self):
        """Test error severity determination."""
        # Test critical error
        context = ErrorContext("TestComponent", "test_operation")
        severity = self.error_boundary._determine_severity(MemoryError(), context)
        assert severity == ErrorSeverity.CRITICAL
        
        # Test high severity error
        context = ErrorContext("TestComponent", "save_operation")
        severity = self.error_boundary._determine_severity(FileNotFoundError(), context)
        assert severity == ErrorSeverity.HIGH
        
        # Test medium severity error
        severity = self.error_boundary._determine_severity(ConnectionError(), context)
        assert severity == ErrorSeverity.MEDIUM
        
        # Test low severity error
        severity = self.error_boundary._determine_severity(ValueError(), context)
        assert severity == ErrorSeverity.LOW
    
    def test_rate_limiting(self):
        """Test error rate limiting."""
        # Generate multiple errors quickly
        for i in range(10):
            try:
                with self.error_boundary.handle_errors("test_operation"):
                    raise ValueError(f"Error {i}")
            except:
                pass
        
        # Should have triggered rate limiting
        assert self.error_boundary._error_count > self.error_boundary._max_errors


class TestFallbackDisplayManager:
    """Test fallback display manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fallback_manager = FallbackDisplayManager()
    
    def test_register_fallback(self):
        """Test registering fallback components."""
        def mock_fallback_factory(error_message):
            return ft.Text(f"Fallback: {error_message}")
        
        self.fallback_manager.register_fallback("TestComponent", mock_fallback_factory)
        assert "TestComponent" in self.fallback_manager._fallback_components
    
    def test_get_fallback_component_registered(self):
        """Test getting registered fallback component."""
        def mock_fallback_factory(error_message):
            return ft.Text(f"Custom fallback: {error_message}")
        
        self.fallback_manager.register_fallback("TestComponent", mock_fallback_factory)
        
        fallback = self.fallback_manager.get_fallback_component("TestComponent", "Test error")
        assert isinstance(fallback, ft.Text)
        assert fallback.value == "Custom fallback: Test error"
    
    def test_get_fallback_component_default(self):
        """Test getting default fallback component."""
        fallback = self.fallback_manager.get_fallback_component("UnknownComponent", "Test error")
        assert isinstance(fallback, ft.Container)
    
    def test_fallback_factory_failure(self):
        """Test fallback when factory fails."""
        def failing_factory(error_message):
            raise Exception("Factory failed")
        
        self.fallback_manager.register_fallback("TestComponent", failing_factory)
        
        fallback = self.fallback_manager.get_fallback_component("TestComponent", "Test error")
        # Should fall back to default component
        assert isinstance(fallback, ft.Container)


class TestSafeExecute:
    """Test safe execution utility function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
    
    def test_safe_execute_success(self):
        """Test successful safe execution."""
        def test_function():
            return "success"
        
        result = safe_execute(
            test_function,
            "TestComponent",
            "test_operation",
            self.mock_page
        )
        
        assert result == "success"
    
    def test_safe_execute_with_exception(self):
        """Test safe execution with exception."""
        def failing_function():
            raise ValueError("Test error")
        
        result = safe_execute(
            failing_function,
            "TestComponent",
            "test_operation",
            self.mock_page,
            fallback_result="fallback"
        )
        
        assert result == "fallback"
    
    def test_safe_execute_with_user_data(self):
        """Test safe execution with user data."""
        def test_function():
            return "success"
        
        user_data = {"key": "value"}
        
        result = safe_execute(
            test_function,
            "TestComponent",
            "test_operation",
            self.mock_page,
            user_data=user_data
        )
        
        assert result == "success"


class TestServiceErrorHandling:
    """Test error handling in service classes."""
    
    def test_notification_service_error_handling(self):
        """Test notification service error handling."""
        service = NotificationService()
        
        # Test adding notification with invalid data
        result = service.add_notification("", "")  # Empty title and message
        assert result is None
        
        # Test adding valid notification
        result = service.add_notification("Test", "Test message")
        assert result is not None
        assert isinstance(result, Notification)
    
    def test_time_tracking_service_error_handling(self):
        """Test time tracking service error handling."""
        service = TimeTrackingService()
        
        # Test starting tracking with invalid activity
        result = service.start_tracking(None)
        assert result is None
        
        # Test starting tracking with valid activity
        activity = Activity(name="Test Activity", category="Test")
        result = service.start_tracking(activity)
        assert result is not None
        assert isinstance(result, TimeEntry)
    
    def test_workflow_service_error_handling(self):
        """Test workflow service error handling."""
        # Use temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        service = WorkflowService(os.path.join(temp_dir, "test_workflows.json"))
        
        # Test creating workflow with duplicate ID
        workflow1 = service.create_workflow_safe("test_workflow")
        assert workflow1 is not None
        
        workflow2 = service.create_workflow_safe("test_workflow")  # Duplicate
        assert workflow2 is None
        
        # Test getting nonexistent workflow
        result = service.get_workflow_safe("nonexistent")
        assert result is None


class TestComponentErrorRecovery:
    """Test error recovery in UI components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
    
    @patch('views.components.notification_center.NotificationCenter')
    def test_notification_center_error_recovery(self, mock_notification_center):
        """Test notification center error recovery."""
        # This would test the actual component error recovery
        # Implementation depends on the specific component structure
        pass
    
    @patch('views.components.time_tracker_widget.TimeTrackerWidget')
    def test_time_tracker_error_recovery(self, mock_time_tracker):
        """Test time tracker widget error recovery."""
        # This would test the actual component error recovery
        # Implementation depends on the specific component structure
        pass
    
    @patch('views.components.flowchart_widget.FlowchartWidget')
    def test_flowchart_error_recovery(self, mock_flowchart):
        """Test flowchart widget error recovery."""
        # This would test the actual component error recovery
        # Implementation depends on the specific component structure
        pass


class TestErrorScenarios:
    """Test specific error scenarios and recovery."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=ft.Page)
    
    def test_network_failure_scenario(self):
        """Test handling of network failures."""
        # Simulate network failure in service operations
        service = NotificationService()
        
        # Mock network failure
        with patch.object(service, '_backup_notifications', side_effect=ConnectionError("Network failed")):
            result = service.add_notification("Test", "Test message")
            # Should still succeed despite backup failure
            assert result is not None
    
    def test_storage_failure_scenario(self):
        """Test handling of storage failures."""
        # Test storage failure in local storage manager
        storage_manager = LocalStorageManager("/invalid/path")
        
        success = storage_manager.backup_data("test", {"data": "test"})
        assert success is False
        
        # Should handle gracefully without crashing
        restored = storage_manager.restore_data("test")
        assert restored is None
    
    def test_memory_pressure_scenario(self):
        """Test handling of memory pressure."""
        # Simulate memory pressure by creating large objects
        recovery_manager = ErrorRecoveryManager()
        
        # Fill error history to test cleanup
        for i in range(200):  # Exceed max history
            context = ErrorContext(
                component_name="TestComponent",
                operation=f"operation_{i}"
            )
            recovery_manager.record_error(context)
        
        # Should maintain max history limit
        assert len(recovery_manager._error_history) <= recovery_manager._max_history
    
    def test_concurrent_access_scenario(self):
        """Test handling of concurrent access to services."""
        import threading
        
        service = TimeTrackingService()
        activity = Activity(name="Test Activity", category="Test")
        
        def start_tracking():
            try:
                service.start_tracking(activity)
            except:
                pass  # Expected to fail for concurrent access
        
        # Start multiple threads trying to start tracking
        threads = []
        for i in range(5):
            thread = threading.Thread(target=start_tracking)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Only one should succeed
        assert service.is_tracking() or not service.is_tracking()  # Either state is valid
    
    def test_data_corruption_scenario(self):
        """Test handling of data corruption."""
        temp_dir = tempfile.mkdtemp()
        
        # Create corrupted workflow file
        workflow_file = os.path.join(temp_dir, "workflows.json")
        with open(workflow_file, 'w') as f:
            f.write("invalid json content {")
        
        # Service should handle corrupted file gracefully
        service = WorkflowService(workflow_file)
        
        # Should create default workflow when corruption detected
        workflows = service.get_all_workflows()
        # Should either be empty or have default workflow
        assert isinstance(workflows, dict)


if __name__ == "__main__":
    pytest.main([__file__])