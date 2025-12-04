"""
PSP Utilities
=============
Utilities for PSP name normalization, consolidation, and mapping.
"""
from typing import Dict, List, Optional
import re

# PSP Consolidation Mapping
# Maps various PSP name variations to a single canonical name for reporting
PSP_CONSOLIDATION_MAP = {
    # CRYPPAY variations - consolidate all to #61 CRYPPAY
    '#61 CRYPPAY': '#61 CRYPPAY',
    '#62 CRYPPAY': '#61 CRYPPAY',
    '#70 CRYPPAY': '#61 CRYPPAY',
    '#70 CRYPPAY 9': '#61 CRYPPAY',
    '#71 CRYPPAY': '#61 CRYPPAY',
    '#72 CRYPPAY': '#61 CRYPPAY',
    'CRYPPAY': '#61 CRYPPAY',
    'CRYPTOPAY': '#61 CRYPPAY',
    
    # SIPAY variations
    'SİPAY': 'SİPAY',
    'SIPAY': 'SİPAY',
    'SİPAY-15': 'SİPAY',
    
    # TETHER variations
    'TETHER': 'TETHER',
    'TETHER MÜŞ.': 'TETHER',
    'TETHER MÜŞTERİ': 'TETHER',
    
    # CPO variations
    'CPO': 'CPO',
    'CPO PY KK': 'CPO PY KK',
    
    # CASHPAY
    '#60 CASHPAY': '#60 CASHPAY',
    'CASHPAY': '#60 CASHPAY',
    
    # Others
    'KUYUMCU': 'KUYUMCU',
    'GÜN SONU USDT': 'GÜN SONU USDT',
    'ATATP': 'ATATP',
    'FILBOX KK': 'FILBOX KK',
}

# PSP Display Names (for frontend)
PSP_DISPLAY_NAMES = {
    '#61 CRYPPAY': '#61 CRYPPAY',
    'SİPAY': 'SİPAY',
    'TETHER': 'TETHER',
    'CPO': 'CPO',
    'CPO PY KK': 'CPO PY KK',
    '#60 CASHPAY': '#60 CASHPAY',
    'KUYUMCU': 'KUYUMCU',
    'GÜN SONU USDT': 'GÜN SONU USDT',
    'ATATP': 'ATATP',
    'FILBOX KK': 'FILBOX KK',
}


def normalize_psp_name(psp_name: str) -> str:
    """
    Normalize a PSP name to its canonical form.
    
    Args:
        psp_name: Raw PSP name from database
        
    Returns:
        Normalized PSP name
        
    Examples:
        >>> normalize_psp_name('#62 CRYPPAY')
        '#61 CRYPPAY'
        >>> normalize_psp_name('SİPAY-15')
        'SİPAY'
    """
    if not psp_name:
        return ''
    
    # Trim whitespace
    psp_name = psp_name.strip()
    
    # Check if we have a direct mapping
    if psp_name in PSP_CONSOLIDATION_MAP:
        return PSP_CONSOLIDATION_MAP[psp_name]
    
    # Try case-insensitive match
    psp_upper = psp_name.upper()
    for key, value in PSP_CONSOLIDATION_MAP.items():
        if key.upper() == psp_upper:
            return value
    
    # Try partial matches for CRYPPAY
    if 'CRYPPAY' in psp_upper or 'CRYPTOPAY' in psp_upper:
        return '#61 CRYPPAY'
    
    # Try partial matches for SIPAY
    if 'SIPAY' in psp_upper or 'SİPAY' in psp_upper:
        return 'SİPAY'
    
    # Try partial matches for TETHER
    if 'TETHER' in psp_upper:
        return 'TETHER'
    
    # Return as-is if no match found
    return psp_name


def get_psp_display_name(psp_name: str) -> str:
    """
    Get the display name for a PSP (for frontend).
    
    Args:
        psp_name: Normalized PSP name
        
    Returns:
        Display name for frontend
    """
    normalized = normalize_psp_name(psp_name)
    return PSP_DISPLAY_NAMES.get(normalized, normalized)


def consolidate_psp_data(psp_data_list: List[Dict]) -> List[Dict]:
    """
    Consolidate PSP data by merging entries with the same normalized name.
    
    This is used to combine multiple CRYPPAY accounts into one for reporting.
    
    Args:
        psp_data_list: List of PSP data dictionaries with 'psp' key
        
    Returns:
        Consolidated list with merged data
        
    Example:
        Input: [
            {'psp': '#61 CRYPPAY', 'total_deposits': 1000},
            {'psp': '#62 CRYPPAY', 'total_deposits': 2000}
        ]
        Output: [
            {'psp': '#61 CRYPPAY', 'total_deposits': 3000}
        ]
    """
    consolidated = {}
    
    for psp_data in psp_data_list:
        original_psp = psp_data.get('psp', '')
        normalized_psp = normalize_psp_name(original_psp)
        
        if normalized_psp not in consolidated:
            # First entry for this normalized PSP
            consolidated[normalized_psp] = {
                'psp': normalized_psp,
                'original_psps': [original_psp],
                'total_deposits': 0.0,
                'total_withdrawals': 0.0,
                'total_commission': 0.0,
                'total_net': 0.0,
                'total_amount': 0.0,
                'transaction_count': 0,
                'opening_balance': 0.0,
                'closing_balance': 0.0,
                'daily_breakdown': [],
            }
        
        # Merge data
        entry = consolidated[normalized_psp]
        entry['original_psps'].append(original_psp)
        entry['total_deposits'] += float(psp_data.get('total_deposits', 0))
        entry['total_withdrawals'] += float(psp_data.get('total_withdrawals', 0))
        entry['total_commission'] += float(psp_data.get('total_commission', 0))
        entry['total_net'] += float(psp_data.get('total_net', 0))
        entry['total_amount'] += float(psp_data.get('total_amount', 0))
        entry['transaction_count'] += int(psp_data.get('transaction_count', 0))
        
        # For opening/closing balance, use the sum (they represent different accounts)
        entry['opening_balance'] += float(psp_data.get('opening_balance', 0))
        entry['closing_balance'] += float(psp_data.get('closing_balance', 0))
        
        # Merge daily breakdowns if present
        if 'daily_breakdown' in psp_data and psp_data['daily_breakdown']:
            entry['daily_breakdown'].extend(psp_data['daily_breakdown'])
    
    # Convert back to list and clean up
    result = []
    for normalized_psp, data in consolidated.items():
        # Remove original_psps from final output (used for debugging only)
        original_psps = data.pop('original_psps')
        
        # Sort and consolidate daily breakdown by date
        if data['daily_breakdown']:
            daily_by_date = {}
            for day in data['daily_breakdown']:
                date = day['date']
                if date not in daily_by_date:
                    daily_by_date[date] = {
                        'date': date,
                        'deposits': 0.0,
                        'withdrawals': 0.0,
                        'commission': 0.0,
                        'net': 0.0,
                        'allocations': 0.0,
                        'kasa_top': 0.0,
                        'devir': 0.0,
                        'transaction_count': 0,
                    }
                
                # Sum up values for the same date
                daily_by_date[date]['deposits'] += float(day.get('deposits', 0))
                daily_by_date[date]['withdrawals'] += float(day.get('withdrawals', 0))
                daily_by_date[date]['commission'] += float(day.get('commission', 0))
                daily_by_date[date]['net'] += float(day.get('net', 0))
                daily_by_date[date]['allocations'] += float(day.get('allocations', 0))
                # For kasa_top and devir, use the last value (they're cumulative)
                daily_by_date[date]['kasa_top'] = float(day.get('kasa_top', 0))
                daily_by_date[date]['devir'] = float(day.get('devir', 0))
                daily_by_date[date]['transaction_count'] += int(day.get('transaction_count', 0))
            
            # Convert back to sorted list
            data['daily_breakdown'] = sorted(daily_by_date.values(), key=lambda x: x['date'])
        
        result.append(data)
    
    # Sort by PSP name
    result.sort(key=lambda x: x['psp'])
    
    return result


def get_psp_commission_rate(psp_name: str) -> Optional[float]:
    """
    Get the appropriate commission rate for a PSP.
    
    This function handles the logic of selecting the correct commission rate
    when multiple rates exist for the same PSP.
    
    Args:
        psp_name: PSP name (will be normalized)
        
    Returns:
        Commission rate as a percentage (e.g., 7.5 for 7.5%), or None if not found
    """
    from app.services.commission_rate_service import CommissionRateService
    from datetime import date
    
    normalized_psp = normalize_psp_name(psp_name)
    
    try:
        rate = CommissionRateService.get_commission_rate_percentage(normalized_psp, date.today())
        return rate
    except Exception:
        return None


def is_tether_psp(psp_name: str) -> bool:
    """
    Check if a PSP is a TETHER variant.
    
    Args:
        psp_name: PSP name
        
    Returns:
        True if PSP is TETHER or variant
    """
    normalized = normalize_psp_name(psp_name)
    return normalized == 'TETHER'


def get_all_psp_variants(canonical_psp: str) -> List[str]:
    """
    Get all variants of a canonical PSP name.
    
    Args:
        canonical_psp: Canonical PSP name (e.g., '#61 CRYPPAY')
        
    Returns:
        List of all variants that map to this canonical name
        
    Example:
        >>> get_all_psp_variants('#61 CRYPPAY')
        ['#61 CRYPPAY', '#62 CRYPPAY', '#70 CRYPPAY', '#70 CRYPPAY 9', '#71 CRYPPAY', '#72 CRYPPAY', 'CRYPPAY', 'CRYPTOPAY']
    """
    variants = []
    for variant, canonical in PSP_CONSOLIDATION_MAP.items():
        if canonical == canonical_psp:
            variants.append(variant)
    return variants

