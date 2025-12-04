"""
Unit tests for enhanced cache service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.enhanced_cache_service import (
    EnhancedCacheService,
    CacheKey,
    CacheStats
)


@pytest.mark.unit
class TestCacheKey:
    """Test CacheKey utility class"""
    
    def test_transaction_list_key(self):
        """Test transaction list cache key generation"""
        key = CacheKey.transaction_list({'client': 'Test'}, page=1, per_page=10)
        
        assert key.startswith('pipeline:transactions:')
        assert isinstance(key, str)
    
    def test_transaction_detail_key(self):
        """Test transaction detail cache key"""
        key = CacheKey.transaction_detail(123)
        
        assert key == 'pipeline:transaction:123'
    
    def test_psp_summary_key(self):
        """Test PSP summary cache key"""
        key = CacheKey.psp_summary('2025-01-01')
        
        assert key == 'pipeline:psp_summary:2025-01-01'
    
    def test_daily_balance_key(self):
        """Test daily balance cache key"""
        key = CacheKey.daily_balance('2025-01-01', 'PSP1')
        
        assert key == 'pipeline:daily_balance:2025-01-01:PSP1'
    
    def test_exchange_rate_key(self):
        """Test exchange rate cache key"""
        key = CacheKey.exchange_rate('USD', '2025-01-01')
        
        assert key == 'pipeline:exchange_rate:USD:2025-01-01'


@pytest.mark.unit
class TestCacheStats:
    """Test CacheStats class"""
    
    def test_cache_stats_initialization(self):
        """Test cache stats initialization"""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
    
    def test_cache_stats_hit_rate_zero(self):
        """Test hit rate calculation with no requests"""
        stats = CacheStats()
        
        assert stats.hit_rate() == 0.0
    
    def test_cache_stats_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20
        
        assert stats.hit_rate() == 80.0
    
    def test_cache_stats_to_dict(self):
        """Test cache stats to dictionary conversion"""
        stats = CacheStats()
        stats.hits = 10
        stats.misses = 5
        
        result = stats.to_dict()
        
        assert result['hits'] == 10
        assert result['misses'] == 5
        assert 'hit_rate' in result


@pytest.mark.unit
class TestEnhancedCacheService:
    """Test EnhancedCacheService"""
    
    def test_cache_service_initialization(self):
        """Test cache service initialization"""
        service = EnhancedCacheService()
        
        assert service is not None
    
    def test_cache_service_with_redis_client(self):
        """Test cache service with Redis client"""
        mock_redis = Mock()
        service = EnhancedCacheService(redis_client=mock_redis)
        
        assert service._redis_client == mock_redis
    
    def test_get_with_redis(self, app):
        """Test get method with Redis"""
        with app.app_context():
            mock_redis_client = Mock()
            mock_redis_client.get.return_value = '{"test": "data"}'
            
            service = EnhancedCacheService(redis_client=mock_redis_client)
            service._redis_initialized = True  # Mark as initialized
            result = service.get('test_key')
            
            assert result is not None
            assert result == {"test": "data"}
            mock_redis_client.get.assert_called_once_with('test_key')
    
    def test_set_with_redis(self, app):
        """Test set method with Redis"""
        with app.app_context():
            mock_redis_client = Mock()
            mock_redis_client.setex.return_value = True
            
            service = EnhancedCacheService(redis_client=mock_redis_client)
            service._redis_initialized = True  # Mark as initialized
            result = service.set('test_key', {'data': 'value'}, ttl=300)
            
            assert result is True
            mock_redis_client.setex.assert_called_once()
    
    def test_delete_with_redis(self, app):
        """Test delete method with Redis"""
        with app.app_context():
            mock_redis_client = Mock()
            mock_redis_client.delete.return_value = 1
            
            service = EnhancedCacheService(redis_client=mock_redis_client)
            service._redis_initialized = True  # Mark as initialized
            result = service.delete('test_key')
            
            assert result is True
            mock_redis_client.delete.assert_called_once_with('test_key')
    
    def test_get_stats(self, app):
        """Test getting cache statistics"""
        with app.app_context():
            service = EnhancedCacheService()
            stats = service.get_stats()
            
            assert isinstance(stats, dict)
            assert 'hits' in stats
            assert 'misses' in stats

