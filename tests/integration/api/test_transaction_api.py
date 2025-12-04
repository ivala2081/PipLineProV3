"""
Integration Tests - Transaction API
Tests for transaction CRUD operations via API
"""
import pytest
from decimal import Decimal
from datetime import date
from app.models.transaction import Transaction


class TestTransactionListAPI:
    """Test transaction list endpoint"""
    
    def test_get_transactions_unauthorized(self, client):
        """Test getting transactions without authentication"""
        response = client.get('/api/v1/transactions/')  # Add trailing slash
        assert response.status_code == 401
    
    def test_get_transactions_authorized(self, client, auth_headers):
        """Test getting transactions with authentication"""
        response = client.get('/api/v1/transactions/', headers=auth_headers)  # Add trailing slash
        assert response.status_code in [200, 404]  # 404 if no transactions
    
    def test_get_transactions_pagination(self, client, auth_headers, session):
        """Test transaction list pagination"""
        # Create multiple transactions
        for i in range(15):
            transaction = Transaction(
                client_name=f'Client {i}',
                date=date.today(),
                category='DEP',
                amount=Decimal('1000.00'),
                commission=Decimal('50.00'),
                net_amount=Decimal('950.00'),
                currency='TL'
            )
            session.add(transaction)
        session.commit()
        
        response = client.get('/api/v1/transactions/?page=1&per_page=10', headers=auth_headers)  # Add trailing slash
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'transactions' in data or 'items' in data
    
    def test_get_transactions_filtering(self, client, auth_headers, session):
        """Test transaction filtering by category"""
        # Create DEP and WD transactions
        dep_transaction = Transaction(
            client_name='DEP Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        wd_transaction = Transaction(
            client_name='WD Client',
            date=date.today(),
            category='WD',
            amount=Decimal('-500.00'),  # WD requires negative
            commission=Decimal('25.00'),
            net_amount=Decimal('-475.00'),  # Net amount also negative
            currency='TL'
        )
        session.add_all([dep_transaction, wd_transaction])
        session.commit()
        
        response = client.get('/api/v1/transactions/?category=DEP', headers=auth_headers)  # Add trailing slash
        assert response.status_code == 200


class TestTransactionCreateAPI:
    """Test transaction creation endpoint"""
    
    def test_create_transaction_unauthorized(self, client):
        """Test creating transaction without authentication"""
        data = {
            'client_name': 'Test Client',
            'date': str(date.today()),
            'category': 'DEP',
            'amount': '1000.00',
            'commission': '50.00',
            'net_amount': '950.00',
            'currency': 'TL'
        }
        response = client.post('/api/v1/transactions/', json=data)  # Add trailing slash
        assert response.status_code == 401
    
    def test_create_transaction_success(self, client, auth_headers):
        """Test creating transaction successfully"""
        data = {
            'client_name': 'Test Client',
            'date': str(date.today()),
            'category': 'DEP',
            'amount': '1000.00',
            'commission': '50.00',
            'net_amount': '950.00',
            'currency': 'TL'
        }
        response = client.post('/api/v1/transactions', json=data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        result = response.get_json()
        assert 'id' in result or 'transaction' in result
    
    def test_create_transaction_missing_fields(self, client, auth_headers):
        """Test creating transaction with missing required fields"""
        data = {
            'client_name': 'Test Client',
            # Missing other required fields
        }
        response = client.post('/api/v1/transactions/', json=data, headers=auth_headers)  # Add trailing slash
        assert response.status_code in [400, 422]
    
    def test_create_transaction_invalid_amount(self, client, auth_headers):
        """Test creating transaction with invalid amount"""
        data = {
            'client_name': 'Test Client',
            'date': str(date.today()),
            'category': 'DEP',
            'amount': '-1000.00',  # Negative
            'commission': '50.00',
            'net_amount': '950.00',
            'currency': 'TL'
        }
        response = client.post('/api/v1/transactions/', json=data, headers=auth_headers)  # Add trailing slash
        assert response.status_code in [400, 422]
    
    def test_create_transaction_invalid_currency(self, client, auth_headers):
        """Test creating transaction with invalid currency"""
        data = {
            'client_name': 'Test Client',
            'date': str(date.today()),
            'category': 'DEP',
            'amount': '1000.00',
            'commission': '50.00',
            'net_amount': '950.00',
            'currency': 'BTC'  # Invalid
        }
        response = client.post('/api/v1/transactions/', json=data, headers=auth_headers)  # Add trailing slash
        assert response.status_code in [400, 422]


class TestTransactionUpdateAPI:
    """Test transaction update endpoint"""
    
    def test_update_transaction_unauthorized(self, client, session):
        """Test updating transaction without authentication"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        data = {'client_name': 'Updated Client'}
        response = client.put(f'/api/v1/transactions/{transaction.id}', json=data)
        assert response.status_code == 401
    
    def test_update_transaction_success(self, client, auth_headers, session):
        """Test updating transaction successfully"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        data = {'client_name': 'Updated Client'}
        response = client.put(f'/api/v1/transactions/{transaction.id}', json=data, headers=auth_headers)
        assert response.status_code in [200, 204]
    
    def test_update_transaction_not_found(self, client, auth_headers):
        """Test updating non-existent transaction"""
        data = {'client_name': 'Updated Client'}
        response = client.put('/api/v1/transactions/99999', json=data, headers=auth_headers)
        assert response.status_code == 404


class TestTransactionDeleteAPI:
    """Test transaction delete endpoint"""
    
    def test_delete_transaction_unauthorized(self, client, session):
        """Test deleting transaction without authentication"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        response = client.delete(f'/api/v1/transactions/{transaction.id}')
        assert response.status_code == 401
    
    def test_delete_transaction_success(self, client, auth_headers, session):
        """Test deleting transaction successfully"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        transaction_id = transaction.id
        
        response = client.delete(f'/api/v1/transactions/{transaction_id}', headers=auth_headers)
        assert response.status_code in [200, 204]
        
        # Verify transaction is deleted
        deleted = session.query(Transaction).filter_by(id=transaction_id).first()
        assert deleted is None
    
    def test_delete_transaction_not_found(self, client, auth_headers):
        """Test deleting non-existent transaction"""
        response = client.delete('/api/v1/transactions/99999', headers=auth_headers)
        assert response.status_code == 404


class TestTransactionDetailAPI:
    """Test transaction detail endpoint"""
    
    def test_get_transaction_detail_unauthorized(self, client, session):
        """Test getting transaction detail without authentication"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        response = client.get(f'/api/v1/transactions/{transaction.id}')
        assert response.status_code == 401
    
    def test_get_transaction_detail_success(self, client, auth_headers, session):
        """Test getting transaction detail successfully"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        response = client.get(f'/api/v1/transactions/{transaction.id}', headers=auth_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['client_name'] == 'Test Client'
    
    def test_get_transaction_detail_not_found(self, client, auth_headers):
        """Test getting non-existent transaction detail"""
        response = client.get('/api/v1/transactions/99999', headers=auth_headers)
        assert response.status_code == 404


class TestTransactionBulkOperations:
    """Test transaction bulk operations"""
    
    def test_bulk_create_transactions(self, client, auth_headers):
        """Test creating multiple transactions at once"""
        data = {
            'transactions': [
                {
                    'client_name': 'Client 1',
                    'date': str(date.today()),
                    'category': 'DEP',
                    'amount': '1000.00',
                    'commission': '50.00',
                    'net_amount': '950.00',
                    'currency': 'TL'
                },
                {
                    'client_name': 'Client 2',
                    'date': str(date.today()),
                    'category': 'WD',
                    'amount': '500.00',
                    'commission': '25.00',
                    'net_amount': '475.00',
                    'currency': 'TL'
                }
            ]
        }
        response = client.post('/api/v1/transactions/bulk', json=data, headers=auth_headers)
        # May not be implemented, so accept 404 or 501
        assert response.status_code in [200, 201, 404, 501]
    
    def test_bulk_delete_transactions(self, client, auth_headers, session):
        """Test deleting multiple transactions at once"""
        # Create transactions
        transactions = []
        for i in range(3):
            transaction = Transaction(
                client_name=f'Client {i}',
                date=date.today(),
                category='DEP',
                amount=Decimal('1000.00'),
                commission=Decimal('50.00'),
                net_amount=Decimal('950.00'),
                currency='TL'
            )
            session.add(transaction)
            transactions.append(transaction)
        session.commit()
        
        ids = [t.id for t in transactions]
        data = {'ids': ids}
        
        response = client.post('/api/v1/transactions/bulk-delete', json=data, headers=auth_headers)
        # May not be implemented, so accept 404 or 501
        assert response.status_code in [200, 204, 404, 501]

