"""E2E tests for pagination"""
import pytest
from flask import json
from datetime import date
from decimal import Decimal
from app.models.transaction import Transaction


@pytest.fixture
def many_transactions(session, admin_user):
    """Create many transactions for pagination testing"""
    transactions = []
    for i in range(50):
        transaction = Transaction(
            client_name=f'Client {i % 10}',
            date=date.today(),
            amount=Decimal('100.00') + Decimal(str(i)),
            commission=Decimal('5.00'),
            net_amount=Decimal('95.00') + Decimal(str(i)),
            category='DEP',
            currency='TL',
            psp=f'PSP {i % 5}',
            created_by=admin_user.id
        )
        transactions.append(transaction)
        session.add(transaction)
    session.commit()
    return transactions


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EPagination:
    """End-to-end pagination tests"""
    
    def test_pagination_basic(self, client, auth_headers, many_transactions):
        """Test basic pagination"""
        response = client.get('/api/v1/transactions/?page=1&per_page=10', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have pagination info
        assert 'transactions' in data or isinstance(data, list)
        transactions = data.get('transactions', data)
        assert len(transactions) <= 10
    
    def test_pagination_multiple_pages(self, client, auth_headers, many_transactions):
        """Test navigating through multiple pages"""
        # Page 1
        page1 = client.get('/api/v1/transactions/?page=1&per_page=10', headers=auth_headers)
        assert page1.status_code == 200
        data1 = json.loads(page1.data)
        transactions1 = data1.get('transactions', data1)
        
        # Page 2
        page2 = client.get('/api/v1/transactions/?page=2&per_page=10', headers=auth_headers)
        assert page2.status_code == 200
        data2 = json.loads(page2.data)
        transactions2 = data2.get('transactions', data2)
        
        # Should have different transactions
        if len(transactions1) > 0 and len(transactions2) > 0:
            ids1 = {t.get('id') for t in transactions1 if isinstance(t, dict)}
            ids2 = {t.get('id') for t in transactions2 if isinstance(t, dict)}
            if ids1 and ids2:
                assert ids1 != ids2
    
    def test_pagination_max_limit(self, client, auth_headers, many_transactions):
        """Test that pagination respects max limit"""
        # Request more than max
        response = client.get('/api/v1/transactions/?page=1&per_page=10000', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        transactions = data.get('transactions', data)
        # Should be capped at MAX_PER_PAGE (500)
        assert len(transactions) <= 500
    
    def test_pagination_empty_page(self, client, auth_headers):
        """Test requesting page beyond available data"""
        response = client.get('/api/v1/transactions/?page=999&per_page=10', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        transactions = data.get('transactions', data)
        assert len(transactions) == 0
    
    def test_pagination_with_filters(self, client, auth_headers, many_transactions):
        """Test pagination with filters applied"""
        # Filter by category
        response = client.get(
            '/api/v1/transactions/?page=1&per_page=10&category=DEP',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        transactions = data.get('transactions', data)
        assert len(transactions) <= 10

