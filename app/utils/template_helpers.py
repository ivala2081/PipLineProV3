"""
Template helper functions for PipLine
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Union
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def legacy_ultimate_tojson(obj):
    """Legacy JSON serialization function"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

def safe_template_data(data):
    """Ensure template data is safe for JSON serialization"""
    if isinstance(data, dict):
        return {k: safe_template_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [safe_template_data(item) for item in data]
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data

def safe_compare(value: Any, operator: str, compare_value: Any) -> bool:
    """
    Safely compare two values with automatic type conversion
    
    Args:
        value: First value to compare
        operator: Comparison operator ('>=', '<=', '>', '<', '==', '!=')
        compare_value: Second value to compare
        
    Returns:
        bool: Result of the comparison
    """
    try:
        # Check if values can be converted to numeric types
        if value is None or compare_value is None:
            return False
        
        # Try to convert both values
        try:
            converted_value1 = _convert_to_numeric(value)
            converted_value2 = _convert_to_numeric(compare_value)
        except (ValueError, TypeError):
            # If conversion fails, return False for comparisons
            return False
        
        # Perform the comparison
        if operator == '>=':
            return converted_value1 >= converted_value2
        elif operator == '<=':
            return converted_value1 <= converted_value2
        elif operator == '>':
            return converted_value1 > converted_value2
        elif operator == '<':
            return converted_value1 < converted_value2
        elif operator == '==':
            return converted_value1 == converted_value2
        elif operator == '!=':
            return converted_value1 != converted_value2
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return False
            
    except Exception as e:
        logger.error(f"Error in safe_compare: {e}")
        return False

def _convert_to_numeric(value: Any) -> Union[Decimal, int, float]:
    """Convert any value to appropriate numeric type"""
    if value is None:
        raise ValueError("Cannot convert None to numeric")
    
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    
    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.-]', '', value.strip())
        if cleaned:
            try:
                return Decimal(cleaned)
            except (ValueError, InvalidOperation):
                raise ValueError(f"Cannot convert string '{value}' to numeric")
        # If string is empty or contains no numbers, raise error
        raise ValueError(f"Cannot convert string '{value}' to numeric")
    
    # Try to convert to float first, then to Decimal
    try:
        return Decimal(str(float(value)))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError(f"Cannot convert {value} to numeric")

def safe_float(value: Any) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        
    Returns:
        float: Converted value or 0.0 if conversion fails
    """
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', value.strip())
            if cleaned:
                return float(cleaned)
        return 0.0
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} to float")
        return 0.0

def safe_decimal(value: Any) -> Decimal:
    """
    Safely convert value to Decimal
    
    Args:
        value: Value to convert
        
    Returns:
        Decimal: Converted value or Decimal('0') if conversion fails
    """
    try:
        if value is None:
            return Decimal('0')
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', value.strip())
            if cleaned:
                return Decimal(cleaned)
        return Decimal('0')
    except (ValueError, TypeError, InvalidOperation):
        logger.warning(f"Could not convert {value} to Decimal")
        return Decimal('0')

def format_number(value: Any, decimal_places: int = 2) -> str:
    """
    Format number with proper decimal places
    
    Args:
        value: Value to format
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted number string
    """
    try:
        numeric_value = safe_float(value)
        return f"{numeric_value:,.{decimal_places}f}"
    except Exception:
        return "0.00"

def format_currency(value: Any, currency: str = "₺", decimal_places: int = 2) -> str:
    """
    Format value as currency
    
    Args:
        value: Value to format
        currency: Currency symbol
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted currency string
    """
    try:
        numeric_value = safe_float(value)
        return f"{currency}{numeric_value:,.{decimal_places}f}"
    except Exception:
        return f"{currency}0.00"

def safe_multiply(value1: Any, value2: Any, result_type: str = "float") -> Union[float, Decimal]:
    """
    Safely multiply two values
    
    Args:
        value1: First value
        value2: Second value
        result_type: Type of result ('float' or 'decimal')
        
    Returns:
        Union[float, Decimal]: Result of multiplication
    """
    try:
        num1 = _convert_to_numeric(value1)
        num2 = _convert_to_numeric(value2)
        result = num1 * num2
        
        if result_type == "float":
            return float(result)
        else:
            return result
    except Exception as e:
        logger.error(f"Error in safe_multiply: {e}")
        return 0.0 if result_type == "float" else Decimal('0')

def safe_add(value1: Any, value2: Any, result_type: str = "float") -> Union[float, Decimal]:
    """
    Safely add two values
    
    Args:
        value1: First value
        value2: Second value
        result_type: Type of result ('float' or 'decimal')
        
    Returns:
        Union[float, Decimal]: Result of addition
    """
    try:
        num1 = _convert_to_numeric(value1)
        num2 = _convert_to_numeric(value2)
        result = num1 + num2
        
        if result_type == "float":
            return float(result)
        else:
            return result
    except Exception as e:
        logger.error(f"Error in safe_add: {e}")
        return 0.0 if result_type == "float" else Decimal('0')

def safe_subtract(value1: Any, value2: Any, result_type: str = "float") -> Union[float, Decimal]:
    """
    Safely subtract two values
    
    Args:
        value1: First value
        value2: Second value
        result_type: Type of result ('float' or 'decimal')
        
    Returns:
        Union[float, Decimal]: Result of subtraction
    """
    try:
        num1 = _convert_to_numeric(value1)
        num2 = _convert_to_numeric(value2)
        result = num1 - num2
        
        if result_type == "float":
            return float(result)
        else:
            return result
    except Exception as e:
        logger.error(f"Error in safe_subtract: {e}")
        return 0.0 if result_type == "float" else Decimal('0')

def safe_divide(value1: Any, value2: Any, result_type: str = "float") -> Union[float, Decimal]:
    """
    Safely divide two values
    
    Args:
        value1: First value
        value2: Second value
        result_type: Type of result ('float' or 'decimal')
        
    Returns:
        Union[float, Decimal]: Result of division
    """
    try:
        num1 = _convert_to_numeric(value1)
        num2 = _convert_to_numeric(value2)
        
        if num2 == 0:
            logger.warning("Division by zero attempted")
            return 0.0 if result_type == "float" else Decimal('0')
        
        result = num1 / num2
        
        if result_type == "float":
            return float(result)
        else:
            return result
    except Exception as e:
        logger.error(f"Error in safe_divide: {e}")
        return 0.0 if result_type == "float" else Decimal('0')
