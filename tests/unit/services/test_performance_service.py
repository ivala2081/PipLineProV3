"""
Unit tests for performance service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.performance_service import PerformanceMonitor, performance_monitor


@pytest.mark.unit
class TestPerformanceMonitor:
    """Test PerformanceMonitor"""
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization"""
        monitor = PerformanceMonitor()
        
        assert monitor is not None
        assert monitor.slow_threshold == 1.0
        assert len(monitor.request_times) == 0
        assert len(monitor.slow_queries) == 0
    
    def test_record_request(self):
        """Test recording request performance"""
        monitor = PerformanceMonitor()
        
        monitor.record_request('/api/test', 0.5, 200)
        
        assert len(monitor.request_times) == 1
        assert monitor.request_times[0]['endpoint'] == '/api/test'
        assert monitor.request_times[0]['duration'] == 0.5
        assert monitor.request_times[0]['status_code'] == 200
    
    def test_record_slow_request(self):
        """Test recording slow request"""
        monitor = PerformanceMonitor()
        
        monitor.record_request('/api/slow', 2.0, 200)
        
        assert len(monitor.slow_queries) == 1
        assert monitor.slow_queries[0]['duration'] == 2.0
    
    @patch('app.services.performance_service.psutil')
    def test_record_system_metrics(self, mock_psutil):
        """Test recording system metrics"""
        monitor = PerformanceMonitor()
        
        # Mock psutil
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.available = 1024 * 1024 * 1024  # 1GB
        mock_memory.used = 1024 * 1024 * 512  # 512MB
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor.record_system_metrics()
        
        assert len(monitor.system_stats) == 1
        assert monitor.system_stats[0]['cpu_percent'] == 50.0
        assert monitor.system_stats[0]['memory_percent'] == 60.0
    
    def test_get_performance_summary_no_data(self):
        """Test getting performance summary with no data"""
        monitor = PerformanceMonitor()
        
        summary = monitor.get_performance_summary()
        
        assert summary['status'] == 'no_data'
        assert 'message' in summary
    
    def test_get_performance_summary_with_data(self):
        """Test getting performance summary with data"""
        monitor = PerformanceMonitor()
        
        # Add some test data
        monitor.record_request('/api/test1', 0.3, 200)
        monitor.record_request('/api/test2', 0.5, 200)
        monitor.record_request('/api/test3', 0.4, 404)
        
        summary = monitor.get_performance_summary()
        
        assert summary['status'] == 'ok'
        assert 'summary' in summary
        assert summary['summary']['total_requests'] == 3
        assert 'avg_response_time' in summary['summary']
        assert 'status_codes' in summary['summary']
    
    @patch('app.services.performance_service.psutil')
    @patch('app.services.performance_service.gc')
    def test_optimize_memory(self, mock_gc, mock_psutil):
        """Test memory optimization"""
        monitor = PerformanceMonitor()
        
        # Mock psutil
        mock_memory_before = Mock()
        mock_memory_before.percent = 80.0
        mock_memory_after = Mock()
        mock_memory_after.percent = 70.0
        mock_psutil.virtual_memory.side_effect = [mock_memory_before, mock_memory_after]
        
        # Mock gc
        mock_gc.collect.return_value = 100
        
        result = monitor.optimize_memory()
        
        assert result['status'] == 'success'
        assert result['memory_before'] == 80.0
        assert result['memory_after'] == 70.0
        assert result['objects_collected'] == 100
        mock_gc.collect.assert_called_once()

