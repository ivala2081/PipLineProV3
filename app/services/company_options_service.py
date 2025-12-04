"""
Service for managing fixed Company options
"""
import logging
from decimal import Decimal
from typing import List, Dict, Any

from app.models.transaction import Transaction
from app.models.config import Option
from app import db

logger = logging.getLogger(__name__)

# Prevent duplicate logging by tracking logged operations
_logged_operations = set()

class CompanyOptionsService:
    """Service for managing fixed Company options"""
    
    @staticmethod
    def get_companies_from_database() -> List[str]:
        """Get all unique companies from transaction database and option table"""
        try:
            # Get distinct companies from transactions
            company_results = db.session.query(Transaction.company).distinct().filter(
                Transaction.company.isnot(None),
                Transaction.company != ''
            ).order_by(Transaction.company).all()
            
            transaction_companies = [result[0] for result in company_results]
            
            # Get companies from option table (for historical data)
            option_results = db.session.query(Option.value).filter(
                Option.field_name == 'company',
                Option.is_active == True
            ).distinct().order_by(Option.value).all()
            
            option_companies = [result[0] for result in option_results]
            
            # Combine and deduplicate
            all_companies = list(set(transaction_companies + option_companies))
            all_companies.sort()
            
            # Log only once per unique result set
            result_key = f"companies_{len(transaction_companies)}_{len(option_companies)}_{len(all_companies)}"
            if result_key not in _logged_operations:
                logger.info(f"Found {len(transaction_companies)} companies in transaction table: {transaction_companies}")
                logger.info(f"Found {len(option_companies)} companies in option table: {option_companies}")
                logger.info(f"Found {len(all_companies)} unique companies total: {all_companies}")
                _logged_operations.add(result_key)
            
            return all_companies
            
        except Exception as e:
            logger.error(f"Error getting companies from database: {e}")
            return []
    
    @staticmethod
    def create_fixed_company_options() -> List[Dict[str, Any]]:
        """Create fixed company options"""
        companies = CompanyOptionsService.get_companies_from_database()
        
        # Remove duplicates while preserving order
        unique_companies = []
        seen = set()
        for company in companies:
            if company not in seen:
                unique_companies.append(company)
                seen.add(company)
        
        fixed_options = []
        for company in unique_companies:
            fixed_options.append({
                'value': company,
                'is_fixed': True
            })
        
        # Log creation only once
        creation_key = f"created_companies_{len(fixed_options)}"
        if creation_key not in _logged_operations:
            logger.info(f"Created {len(fixed_options)} unique fixed company options")
            _logged_operations.add(creation_key)
        
        return fixed_options
