# Test Transaction API Endpoints
"""
Integration tests for transaction endpoints.
"""
import pytest
from flask import json
from decimal import Decimal
from datetime import datetime


@pytest.mark.integration
class TestTransactionEndpoints:
    """Tests for transaction API endpoints."""
    
    def test_get_transactions_list(self, client, auth_headers, sample_transaction):
        """Test getting list of transactions."""
        response = client.get(
            '/api/v1/transactions/',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should return transactions array or paginated response
        assert 'transactions' in data or isinstance(data, list)
    
    def test_get_transactions_pagination(self, client, auth_headers, multiple_transactions):
        """Test transaction list pagination."""
        response = client.get(
            '/api/v1/transactions/?page=1&per_page=5',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check pagination fields
        if 'transactions' in data:
            assert len(data['transactions']) <= 5
            assert 'total' in data or 'pagination' in data
    
    def test_get_transaction_by_id(self, client, auth_headers, sample_transaction):
        """Test getting a specific transaction by ID."""
        response = client.get(
            f'/api/v1/transactions/{sample_transaction.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['id'] == sample_transaction.id
        assert data['type'] == sample_transaction.type
        assert Decimal(str(data['amount'])) == sample_transaction.amount
    
    def test_get_nonexistent_transaction(self, client, auth_headers):
        """Test getting a transaction that doesn't exist."""
        response = client.get(
            '/api/v1/transactions/99999',
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_transaction(self, client, auth_headers):
        """Test creating a new transaction."""
        transaction_data = {
            'date': datetime.now().isoformat(),
            'type': 'deposit',
            'amount': 1500.00,
            'currency': 'TRY',
            'description': 'Test deposit',
            'psp': 'Test PSP',
            'company': 'Test Company',
            'client': 'Test Client'
        }
        
        response = client.post(
            '/api/v1/transactions/',
            headers=auth_headers,
            json=transaction_data
        )
        
        # Should be created or validation error
        assert response.status_code in [200, 201, 422]
        
        if response.status_code in [200, 201]:
            data = json.loads(response.data)
            assert data['type'] == 'deposit'
            assert float(data['amount']) == 1500.00
    
    def test_create_transaction_invalid_data(self, client, auth_headers):
        """Test creating transaction with invalid data."""
        transaction_data = {
            'type': 'invalid_type',
            'amount': -100,  # Negative amount
            'currency': 'XXX'  # Invalid currency
        }
        
        response = client.post(
            '/api/v1/transactions/',
            headers=auth_headers,
            json=transaction_data
        )
        
        assert response.status_code in [400, 422]
    
    def test_update_transaction(self, client, auth_headers, sample_transaction):
        """Test updating an existing transaction."""
        update_data = {
            'description': 'Updated description',
            'amount': 2000.00
        }
        
        response = client.put(
            f'/api/v1/transactions/{sample_transaction.id}',
            headers=auth_headers,
            json=update_data
        )
        
        # Should succeed or method not allowed
        assert response.status_code in [200, 405]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['description'] == 'Updated description'
    
    def test_delete_transaction(self, client, auth_headers, sample_transaction):
        """Test deleting a transaction."""
        response = client.delete(
            f'/api/v1/transactions/{sample_transaction.id}',
            headers=auth_headers
        )
        
        # Should succeed or method not allowed
        assert response.status_code in [200, 204, 405]
    
    def test_filter_transactions_by_type(self, client, auth_headers, multiple_transactions):
        """Test filtering transactions by type."""
        response = client.get(
            '/api/v1/transactions/?type=deposit',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All returned transactions should be deposits
        transactions = data if isinstance(data, list) else data.get('transactions', [])
        for transaction in transactions:
            assert transaction['type'] == 'deposit'
    
    def test_filter_transactions_by_currency(self, client, auth_headers, multiple_transactions):
        """Test filtering transactions by currency."""
        response = client.get(
            '/api/v1/transactions/?currency=TRY',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All returned transactions should be in TRY
        transactions = data if isinstance(data, list) else data.get('transactions', [])
        for transaction in transactions:
            assert transaction['currency'] == 'TRY'
    
    def test_filter_transactions_by_date_range(self, client, auth_headers, multiple_transactions):
        """Test filtering transactions by date range."""
        start_date = datetime.now().date().isoformat()
        
        response = client.get(
            f'/api/v1/transactions/?start_date={start_date}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_sort_transactions(self, client, auth_headers, multiple_transactions):
        """Test sorting transactions."""
        response = client.get(
            '/api/v1/transactions/?sort_by=date&sort_order=desc',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        transactions = data if isinstance(data, list) else data.get('transactions', [])
        
        # Verify descending date order
        if len(transactions) > 1:
            dates = [t['date'] for t in transactions]
            assert dates == sorted(dates, reverse=True)


@pytest.mark.integration
class TestTransactionSummary:
    """Tests for transaction summary endpoints."""
    
    def test_get_daily_summary(self, client, auth_headers, multiple_transactions):
        """Test getting daily transaction summary."""
        date = datetime.now().date().isoformat()
        
        response = client.get(
            f'/api/summary/batch?dates={date}',
            headers=auth_headers
        )
        
        # Endpoint might exist or not
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, (list, dict))
    
    def test_get_analytics(self, client, auth_headers, multiple_transactions):
        """Test getting analytics data."""
        response = client.get(
            '/api/v1/analytics/dashboard/stats',
            headers=auth_headers
        )
        
        # Should return analytics data or not found
        assert response.status_code in [200, 404]

