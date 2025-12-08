"""
Currency utility functions for consistent TRY conversion across the application
"""
from decimal import Decimal


def get_try_amount(transaction, field='amount'):
    """
    Get the TRY-converted amount for a transaction
    
    Args:
        transaction: Transaction object
        field: Field to get ('amount', 'commission', 'net_amount')
        
    Returns:
        Decimal: TRY-converted amount or fallback to original amount
    """
    try_field = f"{field}_try"
    
    # Check if TRY-converted field exists and has a value
    if hasattr(transaction, try_field):
        try_amount = getattr(transaction, try_field)
        if try_amount is not None and try_amount > 0:
            return try_amount
    
    # Fallback to original amount
    original_amount = getattr(transaction, field, 0)
    return original_amount or Decimal('0')


def get_try_amounts(transaction):
    """
    Get all TRY-converted amounts for a transaction
    
    Args:
        transaction: Transaction object
        
    Returns:
        dict: Dictionary with try-converted amounts
    """
    return {
        'amount': get_try_amount(transaction, 'amount'),
        'commission': get_try_amount(transaction, 'commission'),
        'net_amount': get_try_amount(transaction, 'net_amount')
    }


def calculate_try_totals(transactions, fields=['amount', 'commission', 'net_amount']):
    """
    Calculate TRY totals for a list of transactions
    
    Args:
        transactions: List of Transaction objects
        fields: List of fields to calculate totals for
        
    Returns:
        dict: Dictionary with totals for each field
    """
    totals = {}
    
    for field in fields:
        totals[field] = sum(get_try_amount(t, field) for t in transactions)
    
    return totals
