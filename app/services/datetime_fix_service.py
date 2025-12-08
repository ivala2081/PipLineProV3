"""
DateTime Fix Service
Handles datetime-related errors and ensures proper date object conversion
"""
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Union, Optional
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

class DateTimeFixService:
    """Service to handle datetime-related errors and conversions"""
    
    def __init__(self):
        self.error_count = 0
        self.fix_count = 0
    
    def safe_strftime(self, value: Any, format_str: str = '%Y-%m-%d') -> str:
        """Safely format datetime/date objects with strftime"""
        try:
            if value is None:
                return ""
            
            # If it's already a datetime or date object
            if isinstance(value, (datetime, date)):
                return value.strftime(format_str)
            
            # If it's a string, try to parse it
            if isinstance(value, str):
                parsed_date = self.parse_date_string(value)
                if parsed_date:
                    return parsed_date.strftime(format_str)
                else:
                    return value  # Return original string if can't parse
            
            # For any other type, convert to string
            return str(value)
            
        except Exception as e:
            logger.warning(f"strftime error for value {value}: {e}")
            return str(value) if value is not None else ""
    
    def parse_date_string(self, date_string: str) -> Optional[Union[datetime, date]]:
        """Parse various date string formats"""
        if not date_string:
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # Try ISO format parsing
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        return None
    
    def ensure_datetime(self, value: Any) -> Optional[Union[datetime, date]]:
        """Ensure value is a datetime/date object"""
        if value is None:
            return None
        
        if isinstance(value, (datetime, date)):
            return value
        
        if isinstance(value, str):
            return self.parse_date_string(value)
        
        # Try to convert other types
        try:
            return datetime.fromisoformat(str(value))
        except:
            return None
    
    def fix_template_data_dates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix all date fields in template data"""
        try:
            fixed_data = {}
            for key, value in data.items():
                try:
                    if isinstance(value, dict):
                        # Check if this dict represents a custom object that needs to be restored
                        if key in ['analytics', 'client_stats']:
                            fixed_data[key] = self._restore_custom_object(key, value)
                        else:
                            fixed_data[key] = self.fix_template_data_dates(value)
                    elif isinstance(value, list):
                        fixed_data[key] = [self.fix_template_data_dates(item) if isinstance(item, dict) else item for item in value]
                    elif self._is_date_field(key):
                        fixed_data[key] = self.ensure_datetime(value)
                    else:
                        fixed_data[key] = value
                except Exception as e:
                    logger.warning(f"Failed to fix date field {key}: {e}")
                    fixed_data[key] = value
            
            return fixed_data
        except Exception as e:
            logger.error(f"Failed to fix template data dates: {e}")
            return data
    
    def _restore_custom_object(self, obj_type: str, obj_dict: Dict[str, Any]) -> Any:
        """Restore custom objects from dictionaries"""
        try:
            if obj_type == 'analytics':
                from app.routes.transactions import Analytics
                return Analytics(
                    total_clients=obj_dict.get('total_clients', 0),
                    active_clients=obj_dict.get('active_clients', 0),
                    avg_transaction_value=obj_dict.get('avg_transaction_value', 0),
                    top_client_volume=obj_dict.get('top_client_volume', 0)
                )
            elif obj_type == 'client_stats':
                from app.routes.transactions import ClientStats
                return ClientStats(
                    total_clients=obj_dict.get('total_clients', 0),
                    total_volume=obj_dict.get('total_volume', 0),
                    avg_transaction=obj_dict.get('avg_transaction', 0),
                    top_client=obj_dict.get('top_client', 'N/A')
                )
            else:
                return obj_dict
        except Exception as e:
            logger.warning(f"Failed to restore {obj_type} object: {e}")
            return obj_dict
    
    def _is_date_field(self, field_name: str) -> bool:
        """Check if a field name suggests it contains date data"""
        date_keywords = [
            'date', 'time', 'created', 'updated', 'modified', 
            'timestamp', 'start_date', 'end_date', 'due_date',
            'birth', 'anniversary', 'expiry', 'valid_until',
            'last_login', 'last_activity', 'peak_revenue_date',
            'now'  # Add 'now' as it's commonly used for current datetime
        ]
        
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in date_keywords)
    
    def safe_date_format(self, value: Any, format_str: str = '%Y-%m-%d') -> str:
        """Safely format any date-like value"""
        try:
            if value is None:
                return ""
            
            # Try to convert to datetime first
            dt_value = self.ensure_datetime(value)
            if dt_value:
                return dt_value.strftime(format_str)
            
            # If conversion failed, return as string
            return str(value)
            
        except Exception as e:
            logger.warning(f"Date formatting error for {value}: {e}")
            return str(value) if value is not None else ""
    
    def fix_transaction_dates(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix date fields in transaction data"""
        try:
            fixed_transactions = []
            for transaction in transactions:
                fixed_transaction = transaction.copy()
                
                # Fix common date fields
                date_fields = ['date', 'created_at', 'updated_at', 'last_transaction_date']
                for field in date_fields:
                    if field in fixed_transaction:
                        fixed_transaction[field] = self.ensure_datetime(fixed_transaction[field])
                
                fixed_transactions.append(fixed_transaction)
            
            return fixed_transactions
        except Exception as e:
            logger.error(f"Failed to fix transaction dates: {e}")
            return transactions
    
    def fix_client_data_dates(self, clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix date fields in client data"""
        try:
            fixed_clients = []
            for client in clients:
                fixed_client = client.copy()
                
                # Fix common date fields
                date_fields = ['last_transaction_date', 'created_at', 'updated_at']
                for field in date_fields:
                    if field in fixed_client:
                        fixed_client[field] = self.ensure_datetime(fixed_client[field])
                
                fixed_clients.append(fixed_client)
            
            return fixed_clients
        except Exception as e:
            logger.error(f"Failed to fix client data dates: {e}")
            return clients

# Global service instance
datetime_fix_service = DateTimeFixService()

# Convenience functions
def safe_strftime(value: Any, format_str: str = '%Y-%m-%d') -> str:
    """Safely format datetime/date objects"""
    return datetime_fix_service.safe_strftime(value, format_str)

def ensure_datetime(value: Any) -> Optional[Union[datetime, date]]:
    """Ensure value is a datetime/date object"""
    return datetime_fix_service.ensure_datetime(value)

def fix_template_data_dates(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fix all date fields in template data"""
    return datetime_fix_service.fix_template_data_dates(data)

def safe_date_format(value: Any, format_str: str = '%Y-%m-%d') -> str:
    """Safely format any date-like value"""
    return datetime_fix_service.safe_date_format(value, format_str) 