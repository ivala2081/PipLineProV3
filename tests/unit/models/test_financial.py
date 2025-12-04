"""
Unit tests for financial models
"""
import pytest
from datetime import date
from decimal import Decimal
from app.models.financial import PspTrack, DailyBalance, PSPAllocation


@pytest.mark.unit
@pytest.mark.database
class TestPspTrack:
    """Test PspTrack model"""
    
    def test_psp_track_creation(self, session):
        """Test creating PspTrack"""
        psp_track = PspTrack(
            psp_name='SIPAY',
            date=date.today(),
            amount=Decimal('1000.00'),
            commission_rate=Decimal('0.025'),
            commission_amount=Decimal('25.00')
        )
        session.add(psp_track)
        session.commit()
        
        assert psp_track.psp_name == 'SIPAY'
        assert psp_track.amount == Decimal('1000.00')
        assert psp_track.commission_rate == Decimal('0.025')
    
    def test_psp_track_to_dict(self, session):
        """Test PspTrack to_dict method"""
        psp_track = PspTrack(
            psp_name='SIPAY',
            date=date.today(),
            amount=Decimal('1000.00')
        )
        session.add(psp_track)
        session.commit()
        
        result = psp_track.to_dict()
        
        assert isinstance(result, dict)
        assert result['psp_name'] == 'SIPAY'
        assert 'id' in result
        assert 'date' in result
    
    def test_psp_track_repr(self, session):
        """Test PspTrack string representation"""
        psp_track = PspTrack(
            psp_name='SIPAY',
            date=date.today(),
            amount=Decimal('1000.00')
        )
        session.add(psp_track)
        session.commit()
        
        str_repr = str(psp_track)
        assert 'SIPAY' in str_repr


@pytest.mark.unit
@pytest.mark.database
class TestDailyBalance:
    """Test DailyBalance model"""
    
    def test_daily_balance_creation(self, session):
        """Test creating DailyBalance"""
        balance = DailyBalance(
            date=date.today(),
            psp='SIPAY',
            opening_balance=Decimal('5000.00'),
            total_inflow=Decimal('1000.00'),
            total_outflow=Decimal('200.00'),
            closing_balance=Decimal('5800.00')
        )
        session.add(balance)
        session.commit()
        
        assert balance.psp == 'SIPAY'
        assert balance.opening_balance == Decimal('5000.00')
        assert balance.closing_balance == Decimal('5800.00')
    
    def test_daily_balance_to_dict(self, session):
        """Test DailyBalance to_dict method"""
        balance = DailyBalance(
            date=date.today(),
            psp='SIPAY',
            opening_balance=Decimal('5000.00')
        )
        session.add(balance)
        session.commit()
        
        result = balance.to_dict()
        
        assert isinstance(result, dict)
        assert result['psp'] == 'SIPAY'
        assert 'id' in result
        assert 'date' in result
    
    def test_daily_balance_repr(self, session):
        """Test DailyBalance string representation"""
        balance = DailyBalance(
            date=date.today(),
            psp='SIPAY',
            net_amount=Decimal('1000.00')
        )
        session.add(balance)
        session.commit()
        
        str_repr = str(balance)
        assert 'SIPAY' in str_repr or 'DailyBalance' in str_repr


@pytest.mark.unit
@pytest.mark.database
class TestPSPAllocation:
    """Test PSPAllocation model"""
    
    def test_psp_allocation_creation(self, session):
        """Test creating PSPAllocation"""
        allocation = PSPAllocation(
            date=date.today(),
            psp_name='SIPAY',
            allocation_amount=Decimal('1000.00')
        )
        session.add(allocation)
        session.commit()
        
        assert allocation.psp_name == 'SIPAY'
        assert allocation.allocation_amount == Decimal('1000.00')
    
    def test_psp_allocation_to_dict(self, session):
        """Test PSPAllocation to_dict method"""
        allocation = PSPAllocation(
            date=date.today(),
            psp_name='SIPAY',
            allocation_amount=Decimal('1000.00')
        )
        session.add(allocation)
        session.commit()
        
        result = allocation.to_dict()
        
        assert isinstance(result, dict)
        assert result['psp_name'] == 'SIPAY'
        assert 'id' in result

