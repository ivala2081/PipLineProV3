"""
Transaction-based calculation service
"""
from app import db
from app.models.transaction import Transaction
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import func, and_

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service
from app.utils.currency_utils import get_try_amount, get_try_amounts, calculate_try_totals


class TransactionCalculationService:
    """Service for transaction-based calculations"""
    
    @staticmethod
    def get_dashboard_metrics(days=30):
        """Get dashboard metrics based on transaction data"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Calculate basic metrics using TRY-converted amounts
        totals = calculate_try_totals(transactions)
        total_amount = totals['amount']
        total_commission = totals['commission']
        total_net = totals['net_amount']
        transaction_count = len(transactions)
        unique_clients = len(set(t.client_name for t in transactions if t.client_name))
        
        # Calculate growth rates
        prev_start_date = start_date - timedelta(days=days)
        prev_transactions = Transaction.query.filter(
            Transaction.date >= prev_start_date,
            Transaction.date < start_date
        ).all()
        
        prev_totals = calculate_try_totals(prev_transactions, ['amount', 'net_amount'])
        prev_total_amount = prev_totals['amount']
        prev_total_net = prev_totals['net_amount']
        prev_count = len(prev_transactions)
        
        # Calculate growth percentages
        amount_growth = ((total_amount - prev_total_amount) / prev_total_amount * 100) if prev_total_amount > 0 else 0
        net_growth = ((total_net - prev_total_net) / prev_total_net * 100) if prev_total_net > 0 else 0
        count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
        
        return {
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'total_net': float(total_net),
            'transaction_count': transaction_count,
            'unique_clients': unique_clients,
            'amount_growth': float(amount_growth),
            'net_growth': float(net_growth),
            'count_growth': float(count_growth)
        }
    
    @staticmethod
    def get_psp_metrics(days=30):
        """Get PSP metrics based on transaction data"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Group by PSP
        psp_data = defaultdict(lambda: {
            'total_amount': Decimal('0'),
            'total_commission': Decimal('0'),
            'total_net': Decimal('0'),
            'transaction_count': 0,
            'deposits': Decimal('0'),
            'withdrawals': Decimal('0'),
            'active_days': set()
        })
        
        for transaction in transactions:
            psp_name = transaction.psp or 'Unknown'
            # Use TRY-converted amounts for calculations
            amounts = get_try_amounts(transaction)
            
            psp_data[psp_name]['total_amount'] += amounts['amount']
            psp_data[psp_name]['total_commission'] += amounts['commission']
            psp_data[psp_name]['total_net'] += amounts['net_amount']
            psp_data[psp_name]['transaction_count'] += 1
            psp_data[psp_name]['active_days'].add(transaction.date)
            
            # Categorize by transaction type
            if transaction.category in ['Deposit', 'Investment']:
                psp_data[psp_name]['deposits'] += amounts['amount']
            elif transaction.category in ['Withdraw', 'Withdrawal']:
                psp_data[psp_name]['withdrawals'] += amounts['amount']
        
        # Convert to final format
        result = {}
        for psp_name, data in psp_data.items():
            result[psp_name] = {
                'total_allocation': float(data['deposits']),
                'total_rollover': float(data['total_net']),
                'transaction_count': data['transaction_count'],
                'active_days': len(data['active_days']),
                'is_active': data['transaction_count'] > 0
            }
        
        return result
    
    @staticmethod
    def get_daily_summary(days=30):
        """Get daily summary based on transaction data"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Group by date
        daily_data = defaultdict(lambda: {
            'date': None,
            'psps': {},
            'totals': {
                'total_psp': 0,
                'toplam': Decimal('0'),
                'net': Decimal('0'),
                'carry_over': Decimal('0'),
                'komisyon': Decimal('0')
            }
        })
        
        for transaction in transactions:
            psp_name = transaction.psp or 'Unknown'
            
            # Use TRY-converted amounts for calculations
            amounts = get_try_amounts(transaction)
            
            if transaction.date not in daily_data:
                daily_data[transaction.date]['date'] = transaction.date
            
            # Initialize PSP data if not exists
            if psp_name not in daily_data[transaction.date]['psps']:
                daily_data[transaction.date]['psps'][psp_name] = {
                    'yatirim': Decimal('0'),
                    'cekme': Decimal('0'),
                    'toplam': Decimal('0'),
                    'komisyon': Decimal('0'),
                    'net': Decimal('0'),
                    'allocation': Decimal('0'),
                    'rollover': Decimal('0'),
                    'paid': False,
                    'transaction_count': 0
                }
            
            # Update PSP data
            psp_data = daily_data[transaction.date]['psps'][psp_name]
            
            if transaction.category in ['Deposit', 'Investment']:
                psp_data['yatirim'] += amounts['amount']
                psp_data['toplam'] += amounts['amount']
            elif transaction.category in ['Withdraw', 'Withdrawal']:
                psp_data['cekme'] += amounts['amount']
                psp_data['toplam'] -= amounts['amount']
            else:
                psp_data['yatirim'] += amounts['amount']
                psp_data['toplam'] += amounts['amount']
            
            psp_data['komisyon'] += amounts['commission']
            psp_data['net'] = psp_data['toplam'] - psp_data['komisyon']
            psp_data['rollover'] = psp_data['net']
            psp_data['transaction_count'] += 1
            
            # Update daily totals
            daily_data[transaction.date]['totals']['total_psp'] = len(daily_data[transaction.date]['psps'])
            # Only add deposits to daily total, subtract withdrawals
            if transaction.category in ['Deposit', 'Investment']:
                daily_data[transaction.date]['totals']['toplam'] += amounts['amount']
            elif transaction.category in ['Withdraw', 'Withdrawal']:
                daily_data[transaction.date]['totals']['toplam'] -= amounts['amount']
            else:
                daily_data[transaction.date]['totals']['toplam'] += amounts['amount']
            daily_data[transaction.date]['totals']['komisyon'] += amounts['commission']
            daily_data[transaction.date]['totals']['net'] += (amounts['amount'] - amounts['commission'])
            daily_data[transaction.date]['totals']['carry_over'] += (amounts['amount'] - amounts['commission'])
        
        # Convert to list and sort
        result = list(daily_data.values())
        result.sort(key=lambda x: x['date'], reverse=True)
        
        return result