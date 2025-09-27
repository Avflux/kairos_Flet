from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import threading
import time
import logging

from models.activity import Activity
from models.time_entry import TimeEntry
from models.interfaces import TimeTrackingServiceInterface, TimerUpdateListener
from views.components.error_handling import (
    ErrorBoundary, get_recovery_manager, get_storage_manager,
    ErrorSeverity, ErrorContext
)


class TimeTrackingService(TimeTrackingServiceInterface):
    """Service for managing time tracking operations."""
    
    def __init__(self):
        self._current_entry: Optional[TimeEntry] = None
        self._is_paused: bool = False
        self._pause_start_time: Optional[datetime] = None
        self._total_paused_duration: timedelta = timedelta()
        self._time_entries: List[TimeEntry] = []
        self._listeners: List[TimerUpdateListener] = []
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_timer: bool = False
        self._lock = threading.Lock()
        
        # Error handling components
        self._recovery_manager = get_recovery_manager()
        self._storage_manager = get_storage_manager()
        self._backup_interval = 30  # Backup every 30 seconds during tracking
        self._last_backup_time: Optional[datetime] = None
        
        # Register recovery strategies
        self._recovery_manager.register_recovery_strategy(
            'TimerThreadError', self._recover_timer_thread
        )
        self._recovery_manager.register_recovery_strategy(
            'TimeEntryCorruption', self._recover_time_entries
        )
        
        # Restore time entries from backup
        self._restore_time_entries_from_backup()
    
    def add_listener(self, listener: TimerUpdateListener) -> None:
        """Add a listener for timer updates."""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def remove_listener(self, listener: TimerUpdateListener) -> None:
        """Remove a listener for timer updates."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def _notify_listeners_start(self, activity: Activity) -> None:
        """Notify all listeners that timer started."""
        for listener in self._listeners:
            try:
                listener.on_timer_start(activity)
            except Exception:
                # Ignore listener errors to prevent service disruption
                pass
    
    def _notify_listeners_stop(self, time_entry: TimeEntry) -> None:
        """Notify all listeners that timer stopped."""
        for listener in self._listeners:
            try:
                listener.on_timer_stop(time_entry)
            except Exception:
                pass
    
    def _notify_listeners_pause(self) -> None:
        """Notify all listeners that timer paused."""
        for listener in self._listeners:
            try:
                listener.on_timer_pause()
            except Exception:
                pass
    
    def _notify_listeners_resume(self) -> None:
        """Notify all listeners that timer resumed."""
        for listener in self._listeners:
            try:
                listener.on_timer_resume()
            except Exception:
                pass
    
    def _notify_listeners_tick(self, elapsed_time: timedelta) -> None:
        """Notify all listeners of timer tick."""
        for listener in self._listeners:
            try:
                listener.on_timer_tick(elapsed_time)
            except Exception:
                pass
    
    def _start_timer_thread(self) -> None:
        """Start the timer update thread."""
        if self._timer_thread and self._timer_thread.is_alive():
            return
        
        self._stop_timer = False
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()
    
    def _start_timer_thread_safe(self) -> bool:
        """Start the timer thread with error handling."""
        try:
            self._start_timer_thread()
            return True
        except Exception as e:
            logging.error(f"Failed to start timer thread: {e}")
            context = ErrorContext(
                component_name="TimeTrackingService",
                operation="start_timer_thread"
            )
            self._recovery_manager.record_error(context)
            return False
    
    def _stop_timer_thread(self) -> None:
        """Stop the timer update thread."""
        self._stop_timer = True
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=1.0)
    
    def _timer_loop(self) -> None:
        """Main timer loop that runs in a separate thread with error handling."""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while not self._stop_timer:
            try:
                with self._lock:
                    if self._current_entry and not self._is_paused:
                        elapsed_time = self.get_elapsed_time()
                        self._notify_listeners_tick(elapsed_time)
                        
                        # Periodic backup during tracking
                        self._periodic_backup()
                
                consecutive_errors = 0  # Reset error count on success
                time.sleep(1.0)  # Update every second
                
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"Timer loop error (attempt {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logging.critical("Timer loop failed repeatedly, stopping timer")
                    context = ErrorContext(
                        component_name="TimeTrackingService",
                        operation="timer_loop",
                        severity=ErrorSeverity.CRITICAL
                    )
                    self._recovery_manager.record_error(context)
                    break
                
                time.sleep(2.0)  # Wait longer before retry
    
    def start_tracking(self, activity: Activity) -> Optional[TimeEntry]:
        """Start tracking time for an activity with error handling."""
        try:
            with self._lock:
                if self._current_entry is not None:
                    raise ValueError("Time tracking is already active. Stop current tracking first.")
                
                # Validate activity
                if not activity or not activity.id:
                    raise ValueError("Valid activity is required to start tracking")
                
                # Create new time entry
                self._current_entry = TimeEntry(
                    activity_id=activity.id,
                    start_time=datetime.now()
                )
                
                # Reset pause state
                self._is_paused = False
                self._pause_start_time = None
                self._total_paused_duration = timedelta()
                
                # Backup current state
                self._backup_current_session()
                
                # Start timer thread with error handling
                if not self._start_timer_thread_safe():
                    raise RuntimeError("Failed to start timer thread")
                
                # Notify listeners
                self._notify_listeners_start(activity)
                
                logging.info(f"Started tracking activity: {activity.name}")
                return self._current_entry
                
        except Exception as e:
            logging.error(f"Failed to start tracking: {e}")
            context = ErrorContext(
                component_name="TimeTrackingService",
                operation="start_tracking",
                user_data={"activity_id": activity.id if activity else None}
            )
            self._recovery_manager.record_error(context)
            
            # Clean up partial state
            self._current_entry = None
            self._is_paused = False
            self._stop_timer_thread()
            
            return None
    
    def stop_tracking(self) -> Optional[TimeEntry]:
        """Stop current time tracking. Returns the completed time entry."""
        with self._lock:
            if self._current_entry is None:
                return None
            
            # If paused, add the current pause duration
            if self._is_paused and self._pause_start_time:
                self._total_paused_duration += datetime.now() - self._pause_start_time
            
            # Stop the time entry
            stop_time = datetime.now()
            self._current_entry.stop(stop_time)
            
            # Store the completed entry
            completed_entry = self._current_entry
            self._time_entries.append(completed_entry)
            
            # Reset state
            self._current_entry = None
            self._is_paused = False
            self._pause_start_time = None
            self._total_paused_duration = timedelta()
            
            # Stop timer thread
            self._stop_timer_thread()
            
            # Notify listeners
            self._notify_listeners_stop(completed_entry)
            
            return completed_entry
    
    def pause_tracking(self) -> bool:
        """Pause current time tracking. Returns True if successful."""
        with self._lock:
            if self._current_entry is None or self._is_paused:
                return False
            
            self._is_paused = True
            self._pause_start_time = datetime.now()
            
            # Notify listeners
            self._notify_listeners_pause()
            
            return True
    
    def resume_tracking(self) -> bool:
        """Resume paused time tracking. Returns True if successful."""
        with self._lock:
            if self._current_entry is None or not self._is_paused:
                return False
            
            # Add the pause duration to total paused time
            if self._pause_start_time:
                self._total_paused_duration += datetime.now() - self._pause_start_time
            
            self._is_paused = False
            self._pause_start_time = None
            
            # Notify listeners
            self._notify_listeners_resume()
            
            return True
    
    def get_current_entry(self) -> Optional[TimeEntry]:
        """Get the currently active time entry."""
        with self._lock:
            return self._current_entry
    
    def get_time_entries(self, activity_id: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries, optionally filtered by activity."""
        with self._lock:
            if activity_id is None:
                return self._time_entries.copy()
            
            return [entry for entry in self._time_entries if entry.activity_id == activity_id]
    
    def is_tracking(self) -> bool:
        """Check if time tracking is currently active."""
        with self._lock:
            return self._current_entry is not None
    
    def is_paused(self) -> bool:
        """Check if time tracking is currently paused."""
        with self._lock:
            return self._is_paused
    
    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time for current tracking session."""
        with self._lock:
            if self._current_entry is None:
                return timedelta()
            
            current_time = datetime.now()
            total_elapsed = current_time - self._current_entry.start_time
            
            # Subtract paused time
            paused_time = self._total_paused_duration
            if self._is_paused and self._pause_start_time:
                paused_time += current_time - self._pause_start_time
            
            return total_elapsed - paused_time
    
    def get_current_activity_id(self) -> Optional[str]:
        """Get the ID of the currently tracked activity."""
        with self._lock:
            return self._current_entry.activity_id if self._current_entry else None
    
    def clear_all_entries(self) -> int:
        """Clear all time entries. Returns count of entries cleared."""
        with self._lock:
            count = len(self._time_entries)
            self._time_entries.clear()
            return count
    
    def get_total_time_for_activity(self, activity_id: str) -> timedelta:
        """Get total time tracked for a specific activity."""
        with self._lock:
            total = timedelta()
            for entry in self._time_entries:
                if entry.activity_id == activity_id and entry.end_time:
                    total += entry.duration
            
            # Add current session if tracking the same activity
            if (self._current_entry and 
                self._current_entry.activity_id == activity_id):
                total += self.get_elapsed_time()
            
            return total
    
    def get_daily_total(self, date: Optional[datetime] = None) -> timedelta:
        """Get total time tracked for a specific date (defaults to today)."""
        if date is None:
            date = datetime.now()
        
        target_date = date.date()
        
        with self._lock:
            total = timedelta()
            for entry in self._time_entries:
                if entry.start_time.date() == target_date and entry.end_time:
                    total += entry.duration
            
            # Add current session if it's from today
            if (self._current_entry and 
                self._current_entry.start_time.date() == target_date):
                total += self.get_elapsed_time()
            
            return total
            
    def _backup_current_session(self) -> None:
        """Backup current tracking session."""
        try:
            if self._current_entry:
                session_data = {
                    'current_entry': {
                        'id': self._current_entry.id,
                        'activity_id': self._current_entry.activity_id,
                        'start_time': self._current_entry.start_time.isoformat(),
                        'notes': self._current_entry.notes
                    },
                    'is_paused': self._is_paused,
                    'pause_start_time': self._pause_start_time.isoformat() if self._pause_start_time else None,
                    'total_paused_duration': self._total_paused_duration.total_seconds()
                }
                
                self._storage_manager.backup_data('current_session', session_data)
                self._last_backup_time = datetime.now()
        except Exception as e:
            logging.error(f"Failed to backup current session: {e}")
    
    def _periodic_backup(self) -> None:
        """Perform periodic backup during tracking."""
        try:
            now = datetime.now()
            if (self._last_backup_time is None or 
                (now - self._last_backup_time).total_seconds() >= self._backup_interval):
                self._backup_current_session()
                self._backup_time_entries()
        except Exception as e:
            logging.error(f"Periodic backup failed: {e}")
    
    def _backup_time_entries(self) -> None:
        """Backup all time entries."""
        try:
            entries_data = [
                {
                    'id': entry.id,
                    'activity_id': entry.activity_id,
                    'start_time': entry.start_time.isoformat(),
                    'end_time': entry.end_time.isoformat() if entry.end_time else None,
                    'duration': entry.duration.total_seconds() if entry.duration else 0,
                    'notes': entry.notes
                }
                for entry in self._time_entries
            ]
            
            self._storage_manager.backup_data('time_entries', entries_data)
        except Exception as e:
            logging.error(f"Failed to backup time entries: {e}")
    
    def _restore_time_entries_from_backup(self) -> None:
        """Restore time entries from backup."""
        try:
            # Restore completed time entries
            entries_data = self._storage_manager.restore_data('time_entries')
            if entries_data:
                for item in entries_data:
                    try:
                        entry = TimeEntry(
                            id=item['id'],
                            activity_id=item['activity_id'],
                            start_time=datetime.fromisoformat(item['start_time']),
                            notes=item.get('notes')
                        )
                        
                        if item.get('end_time'):
                            entry.end_time = datetime.fromisoformat(item['end_time'])
                            entry.duration = timedelta(seconds=item.get('duration', 0))
                        
                        self._time_entries.append(entry)
                    except Exception as e:
                        logging.warning(f"Failed to restore time entry: {e}")
                
                logging.info(f"Restored {len(self._time_entries)} time entries from backup")
            
            # Restore current session if exists
            session_data = self._storage_manager.restore_data('current_session')
            if session_data:
                try:
                    entry_data = session_data['current_entry']
                    self._current_entry = TimeEntry(
                        id=entry_data['id'],
                        activity_id=entry_data['activity_id'],
                        start_time=datetime.fromisoformat(entry_data['start_time']),
                        notes=entry_data.get('notes')
                    )
                    
                    self._is_paused = session_data.get('is_paused', False)
                    if session_data.get('pause_start_time'):
                        self._pause_start_time = datetime.fromisoformat(session_data['pause_start_time'])
                    
                    self._total_paused_duration = timedelta(seconds=session_data.get('total_paused_duration', 0))
                    
                    # Restart timer if session was active
                    if not self._is_paused:
                        self._start_timer_thread_safe()
                    
                    logging.info("Restored active tracking session from backup")
                except Exception as e:
                    logging.warning(f"Failed to restore current session: {e}")
                    # Clear corrupted session backup
                    self._storage_manager.clear_backup('current_session')
        
        except Exception as e:
            logging.error(f"Failed to restore from backup: {e}")
    
    def _recover_timer_thread(self, context: ErrorContext) -> bool:
        """Recovery strategy for timer thread errors."""
        try:
            # Stop current thread if running
            self._stop_timer_thread()
            
            # Wait a moment for cleanup
            time.sleep(1.0)
            
            # Restart timer thread if we have an active entry
            if self._current_entry and not self._is_paused:
                return self._start_timer_thread_safe()
            
            return True
        except Exception as e:
            logging.error(f"Timer thread recovery failed: {e}")
            return False
    
    def _recover_time_entries(self, context: ErrorContext) -> bool:
        """Recovery strategy for time entry corruption."""
        try:
            # Backup current state before recovery
            corrupted_entries = self._time_entries.copy()
            self._storage_manager.backup_data('corrupted_entries', corrupted_entries)
            
            # Clear current entries
            self._time_entries.clear()
            
            # Restore from backup
            self._restore_time_entries_from_backup()
            
            return True
        except Exception as e:
            logging.error(f"Time entries recovery failed: {e}")
            return False
    
    def cleanup_session_backup(self) -> None:
        """Clean up session backup when tracking is properly stopped."""
        try:
            self._storage_manager.clear_backup('current_session')
        except Exception as e:
            logging.error(f"Failed to cleanup session backup: {e}")