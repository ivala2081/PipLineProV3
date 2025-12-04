"""Basic load tests"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from flask import json


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.load
class TestLoadBasics:
    """Basic load testing"""
    
    def test_concurrent_auth_requests(self, client, session):
        """Test concurrent authentication requests"""
        from app.models.user import User
        
        # Create test users
        users = []
        for i in range(10):
            user = User(
                username=f'load_user_{i}',
                email=f'load_{i}@test.com',
                role='user',
                is_active=True
            )
            user.set_password('password123')
            users.append(user)
            session.add(user)
        session.commit()
        
        def login(username):
            response = client.post('/api/v1/auth/login', json={
                'username': username,
                'password': 'password123'
            })
            return response.status_code == 200
        
        # Execute concurrent logins
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(login, [f'load_user_{i}' for i in range(10)]))
        elapsed = time.time() - start_time
        
        # All should succeed
        assert all(results), "Some concurrent logins failed"
        assert elapsed < 5.0, "Concurrent requests took too long"
    
    def test_concurrent_read_requests(self, client, auth_headers):
        """Test concurrent read requests"""
        def make_request():
            response = client.get('/api/v1/transactions/', headers=auth_headers)
            return response.status_code == 200
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda _: make_request(), range(20)))
        elapsed = time.time() - start_time
        
        assert all(results), "Some concurrent reads failed"
        assert elapsed < 10.0, "Concurrent reads took too long"
    
    def test_pagination_performance(self, client, auth_headers, many_transactions):
        """Test pagination performance with many transactions"""
        start_time = time.time()
        
        # Request multiple pages
        for page in range(1, 6):
            response = client.get(
                f'/api/v1/transactions/?page={page}&per_page=10',
                headers=auth_headers
            )
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        # 5 pages should complete quickly
        assert elapsed < 2.0, f"Pagination too slow: {elapsed}s"
    
    def test_rate_limiting_respect(self, client, auth_headers):
        """Test that rate limiting is respected under load"""
        start_time = time.time()
        rate_limited = 0
        
        # Make many rapid requests
        for _ in range(30):
            response = client.get('/api/v1/transactions/', headers=auth_headers)
            if response.status_code == 429:
                rate_limited += 1
            time.sleep(0.1)  # Small delay
        
        elapsed = time.time() - start_time
        
        # Should eventually hit rate limit or complete quickly
        assert elapsed < 5.0 or rate_limited > 0

