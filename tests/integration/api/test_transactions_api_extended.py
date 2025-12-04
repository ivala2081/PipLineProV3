"""
Extended integration tests for transactions API
"""
import pytest
from decimal import Decimal
from datetime import date
from app.models.transaction import Transaction


@pytest.mark.integration
@pytest.mark.database
class TestTransactionsAPIExtended:
    """Extended tests for transactions API endpoints"""
    
    def test_create_transaction_with_all_fields(self, client, admin_user, session):
        """Test creating transaction with all fields"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        data = {
            'client_name': 'Test Client Full',
            'amount': 1000.00,
            'currency': 'TL',
            'date': date.today().isoformat(),
            'category': 'DEP',
            'psp': 'SIPAY',
            'payment_method': 'KK',
            'commission': 25.00,
            'notes': 'Test transaction with all fields'
        }
        
        response = client.post('/api/v1/transactions/', json=data)
        
        assert response.status_code in [200, 201]
        response_data = response.get_json()
        assert "data" in response_data or "transaction" in response_data or "id" in response_data
    
    def test_get_transaction_by_id(self, client, admin_user, session):
        """Test getting transaction by ID"""
        # Create a transaction first
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP"
        )
        session.add(transaction)
        session.commit()
        transaction_id = transaction.id
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get(f'/api/v1/transactions/{transaction_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or "id" in data or "client_name" in data
    
    def test_get_transactions_with_pagination(self, client, admin_user, session):
        """Test getting transactions with pagination"""
        # Create multiple transactions
        for i in range(5):
            transaction = Transaction(
                client_name=f"Client {i}",
                amount=Decimal(f"{(i+1)*100}.00"),
                currency="TL",
                date=date.today(),
                category="DEP"
            )
            session.add(transaction)
        session.commit()
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/transactions/?page=1&per_page=2')
        
        assert response.status_code == 200
        data = response.get_json()
        # Check for pagination or data structure
        assert "data" in data or "transactions" in data or isinstance(data, list)
    
    def test_get_transactions_with_filters(self, client, admin_user, session):
        """Test getting transactions with filters"""
        # Create test transactions
        transaction1 = Transaction(
            client_name="Client A",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            psp="PSP1"
        )
        transaction2 = Transaction(
            client_name="Client B",
            amount=Decimal("2000.00"),
            currency="USD",
            date=date.today(),
            category="WD",
            psp="PSP2"
        )
        session.add(transaction1)
        session.add(transaction2)
        session.commit()
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Filter by currency
        response = client.get('/api/v1/transactions/?currency=TL')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or "transactions" in data or isinstance(data, list)
    
    def test_update_transaction(self, client, admin_user, session):
        """Test updating transaction"""
        # Create a transaction
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP"
        )
        session.add(transaction)
        session.commit()
        transaction_id = transaction.id
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Update transaction
        update_data = {
            'amount': 2000.00,
            'notes': 'Updated transaction'
        }
        
        response = client.put(f'/api/v1/transactions/{transaction_id}', json=update_data)
        
        assert response.status_code in [200, 204]
    
    def test_delete_transaction(self, client, admin_user, session):
        """Test deleting transaction"""
        # Create a transaction
        transaction = Transaction(
            client_name="Test Client Delete",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP"
        )
        session.add(transaction)
        session.commit()
        transaction_id = transaction.id
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Delete transaction
        response = client.delete(f'/api/v1/transactions/{transaction_id}')
        
        assert response.status_code in [200, 204, 204]

