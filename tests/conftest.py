# Shared pytest fixtures
import pytest
from decimal import Decimal
from datetime import datetime, timedelta


class _Txn:
    def __init__(self, t_type, amount, date=None):
        self.type = t_type
        self.amount = Decimal(str(amount))
        self.date = date or datetime.now()


@pytest.fixture
def multiple_transactions():
    """A mixed set of deposit and withdrawal transactions for today."""
    today = datetime.now()
    return [
        _Txn('deposit', '100.00', today),
        _Txn('deposit', '250.50', today),
        _Txn('withdrawal', '75.25', today),
        _Txn('deposit', '10.00', today - timedelta(days=1)),  # previous day
    ]

"""Pytest configuration and fixtures"""
import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    app = create_app(config_name='testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def session(app):
    """Database session"""
    with app.app_context():
        yield db.session


@pytest.fixture
def admin_user(session):
    """Create admin user for testing"""
    user = User(
        username='admin',
        email='admin@test.com',
        role='admin',
        admin_level=1,  # 1 = main_admin
        is_active=True
    )
    user.set_password('admin123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def regular_user(session):
    """Create regular user for testing"""
    user = User(
        username='user',
        email='user@test.com',
        role='user',
        is_active=True
    )
    user.set_password('user123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def auth_headers(client, admin_user):
    """Get auth headers for authenticated requests"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    data = response.get_json()
    token = data.get('access_token') or data.get('token')
    return {'Authorization': f'Bearer {token}'} if token else {}


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin token"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    data = response.get_json()
    return data.get('access_token') or data.get('token')


@pytest.fixture
def user_token(client, regular_user):
    """Get regular user token"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'user',
        'password': 'user123'
    })
    data = response.get_json()
    return data.get('access_token') or data.get('token')


@pytest.fixture
def sample_transaction(session):
    """Create a sample transaction for testing"""
    from app.models.transaction import Transaction
    from datetime import date
    from decimal import Decimal
    
    transaction = Transaction(
        client_name='Test Client',
        company='Test Company',
        payment_method='Bank Transfer',
        date=date.today(),
        category='DEP',
        amount=Decimal('1000.00'),
        commission=Decimal('50.00'),
        net_amount=Decimal('950.00'),
        currency='TL',
        psp='Test PSP',
        notes='Test transaction'
    )
    session.add(transaction)
    session.commit()
    return transaction


@pytest.fixture
def sample_transactions(session):
    """Create multiple sample transactions for testing"""
    from app.models.transaction import Transaction
    from datetime import date, timedelta
    from decimal import Decimal
    
    transactions = []
    base_date = date.today()
    
    # Create 5 transactions
    for i in range(5):
        transaction = Transaction(
            client_name=f'Client {i+1}',
            company='Test Company',
            payment_method='Bank Transfer',
            date=base_date - timedelta(days=i),
            category='DEP' if i % 2 == 0 else 'WD',
            amount=Decimal(f'{(i+1)*100}.00'),
            commission=Decimal(f'{(i+1)*5}.00'),
            net_amount=Decimal(f'{(i+1)*95}.00'),
            currency='TL',
            psp=f'PSP {i % 2 + 1}',
            notes=f'Test transaction {i+1}'
        )
        session.add(transaction)
        transactions.append(transaction)
    
    session.commit()
    return transactions


@pytest.fixture
def sample_exchange_rate(session):
    """Create a sample exchange rate for testing"""
    from app.models.config import ExchangeRate
    from datetime import date
    from decimal import Decimal
    
    rate = ExchangeRate(
        currency='USD',
        rate=Decimal('30.5000'),
        date=date.today()
    )
    session.add(rate)
    session.commit()
    return rate


@pytest.fixture
def mock_external_api(monkeypatch):
    """Mock external API responses"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return {'rate': 30.5}
            
            def raise_for_status(self):
                pass
        
        return MockResponse()
    
    monkeypatch.setattr('requests.get', mock_get)


@pytest.fixture
def clean_database(session):
    """Clean database after test"""
    yield
    # Cleanup after test
    from app.models.transaction import Transaction
    from app.models.financial import PspTrack, DailyBalance
    
    session.query(Transaction).delete()
    session.query(PspTrack).delete()
    session.query(DailyBalance).delete()
    session.commit()
