"""
Decimal/Float Type Mismatch Fix Service
Automatically handles type conversions between Decimal and Float to prevent errors
"""

import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union, Any, Optional, Dict, List
import functools
import inspect

logger = logging.getLogger(__name__)

class DecimalFloatFixService:
    """Service to handle Decimal/Float type mismatches automatically"""
    
    def __init__(self):
        self.conversion_stats = {
            'decimal_to_float': 0,
            'float_to_decimal': 0,
            'string_to_decimal': 0,
            'string_to_float': 0,
            'errors': 0
        }
    
    def safe_decimal(self, value: Any, default: Union[Decimal, float, str] = Decimal('0')) -> Decimal:
        """
        Safely convert any value to Decimal
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Decimal object
        """
        if value is None:
            return self._to_decimal(default)
        
        if isinstance(value, Decimal):
            return value
        
        if isinstance(value, (int, float)):
            try:
                self.conversion_stats['float_to_decimal'] += 1
                return Decimal(str(value))
            except (InvalidOperation, ValueError) as e:
                logger.warning(f"Failed to convert {value} to Decimal: {e}")
                self.conversion_stats['errors'] += 1
                return self._to_decimal(default)
        
        if isinstance(value, str):
            try:
                self.conversion_stats['string_to_decimal'] += 1
                return Decimal(value.strip())
            except (InvalidOperation, ValueError) as e:
                logger.warning(f"Failed to convert string '{value}' to Decimal: {e}")
                self.conversion_stats['errors'] += 1
                return self._to_decimal(default)
        
        # Try to convert to string first
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Failed to convert {type(value).__name__} '{value}' to Decimal: {e}")
            self.conversion_stats['errors'] += 1
            return self._to_decimal(default)
    
    def safe_float(self, value: Any, default: Union[float, Decimal, str] = 0.0) -> float:
        """
        Safely convert any value to float
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            float value
        """
        if value is None:
            return self._to_float(default)
        
        if isinstance(value, float):
            return value
        
        if isinstance(value, (int, Decimal)):
            try:
                self.conversion_stats['decimal_to_float'] += 1
                return float(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert {value} to float: {e}")
                self.conversion_stats['errors'] += 1
                return self._to_float(default)
        
        if isinstance(value, str):
            try:
                self.conversion_stats['string_to_float'] += 1
                return float(value.strip())
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert string '{value}' to float: {e}")
                self.conversion_stats['errors'] += 1
                return self._to_float(default)
        
        # Try to convert to string first
        try:
            return float(str(value))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {type(value).__name__} '{value}' to float: {e}")
            self.conversion_stats['errors'] += 1
            return self._to_float(default)
    
    def safe_multiply(self, a: Any, b: Any, result_type: str = 'decimal') -> Union[Decimal, float]:
        """
        Safely multiply two values, handling type mismatches
        
        Args:
            a: First value
            b: Second value
            result_type: 'decimal' or 'float' for result type
            
        Returns:
            Result of multiplication in specified type
        """
        try:
            if result_type.lower() == 'decimal':
                decimal_a = self.safe_decimal(a)
                decimal_b = self.safe_decimal(b)
                return decimal_a * decimal_b
            else:
                float_a = self.safe_float(a)
                float_b = self.safe_float(b)
                return float_a * float_b
        except Exception as e:
            logger.error(f"Error in safe_multiply({a}, {b}, {result_type}): {e}")
            return self.safe_decimal(0) if result_type.lower() == 'decimal' else 0.0
    
    def safe_add(self, a: Any, b: Any, result_type: str = 'decimal') -> Union[Decimal, float]:
        """
        Safely add two values, handling type mismatches
        
        Args:
            a: First value
            b: Second value
            result_type: 'decimal' or 'float' for result type
            
        Returns:
            Result of addition in specified type
        """
        try:
            if result_type.lower() == 'decimal':
                decimal_a = self.safe_decimal(a)
                decimal_b = self.safe_decimal(b)
                return decimal_a + decimal_b
            else:
                float_a = self.safe_float(a)
                float_b = self.safe_float(b)
                return float_a + float_b
        except Exception as e:
            logger.error(f"Error in safe_add({a}, {b}, {result_type}): {e}")
            return self.safe_decimal(0) if result_type.lower() == 'decimal' else 0.0
    
    def safe_subtract(self, a: Any, b: Any, result_type: str = 'decimal') -> Union[Decimal, float]:
        """
        Safely subtract two values, handling type mismatches
        
        Args:
            a: First value
            b: Second value
            result_type: 'decimal' or 'float' for result type
            
        Returns:
            Result of subtraction in specified type
        """
        try:
            if result_type.lower() == 'decimal':
                decimal_a = self.safe_decimal(a)
                decimal_b = self.safe_decimal(b)
                return decimal_a - decimal_b
            else:
                float_a = self.safe_float(a)
                float_b = self.safe_float(b)
                return float_a - float_b
        except Exception as e:
            logger.error(f"Error in safe_subtract({a}, {b}, {result_type}): {e}")
            return self.safe_decimal(0) if result_type.lower() == 'decimal' else 0.0
    
    def safe_divide(self, a: Any, b: Any, result_type: str = 'decimal', precision: int = 2) -> Union[Decimal, float]:
        """
        Safely divide two values, handling type mismatches
        
        Args:
            a: First value
            b: Second value
            result_type: 'decimal' or 'float' for result type
            precision: Decimal places for rounding (Decimal only)
            
        Returns:
            Result of division in specified type
        """
        try:
            if result_type.lower() == 'decimal':
                decimal_a = self.safe_decimal(a)
                decimal_b = self.safe_decimal(b)
                if decimal_b == 0:
                    logger.warning("Division by zero attempted")
                    return Decimal('0')
                result = decimal_a / decimal_b
                return result.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)
            else:
                float_a = self.safe_float(a)
                float_b = self.safe_float(b)
                if float_b == 0:
                    logger.warning("Division by zero attempted")
                    return 0.0
                return float_a / float_b
        except Exception as e:
            logger.error(f"Error in safe_divide({a}, {b}, {result_type}): {e}")
            return self.safe_decimal(0) if result_type.lower() == 'decimal' else 0.0
    
    def convert_for_template(self, value: Any, target_type: str = 'float') -> Union[Decimal, float]:
        """
        Convert value for template use (safe for display)
        
        Args:
            value: Value to convert
            target_type: 'decimal' or 'float'
            
        Returns:
            Converted value safe for template use
        """
        try:
            if target_type.lower() == 'decimal':
                return self.safe_decimal(value)
            else:
                return self.safe_float(value)
        except Exception as e:
            logger.error(f"Error converting {value} for template: {e}")
            return 0.0 if target_type.lower() == 'float' else Decimal('0')
    
    def _to_decimal(self, value: Any) -> Decimal:
        """Internal helper to convert to Decimal"""
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal('0')
    
    def _to_float(self, value: Any) -> float:
        """Internal helper to convert to float"""
        try:
            if isinstance(value, float):
                return value
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def get_conversion_stats(self) -> Dict[str, int]:
        """Get conversion statistics"""
        return self.conversion_stats.copy()
    
    def reset_stats(self):
        """Reset conversion statistics"""
        self.conversion_stats = {
            'decimal_to_float': 0,
            'float_to_decimal': 0,
            'string_to_decimal': 0,
            'string_to_float': 0,
            'errors': 0
        }

# Global instance
decimal_float_service = DecimalFloatFixService()

def auto_convert_types(func):
    """
    Decorator to automatically handle Decimal/Float type conversions
    
    Usage:
        @auto_convert_types
        def my_function(amount, rate):
            return amount * rate  # Will automatically handle type conversion
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Convert numeric arguments automatically
            converted_args = []
            for param_name, param_value in bound_args.arguments.items():
                param_info = sig.parameters[param_name]
                
                # Check if parameter has type hints
                if hasattr(param_info.annotation, '__name__'):
                    if param_info.annotation.__name__ == 'Decimal':
                        converted_args.append(decimal_float_service.safe_decimal(param_value))
                    elif param_info.annotation.__name__ == 'float':
                        converted_args.append(decimal_float_service.safe_float(param_value))
                    else:
                        converted_args.append(param_value)
                else:
                    converted_args.append(param_value)
            
            # Call original function with converted arguments
            return func(*converted_args)
            
        except Exception as e:
            logger.error(f"Error in auto_convert_types decorator for {func.__name__}: {e}")
            raise
    
    return wrapper

def safe_numeric_operation(operation: str = 'multiply', result_type: str = 'decimal'):
    """
    Decorator factory for safe numeric operations
    
    Usage:
        @safe_numeric_operation('multiply', 'decimal')
        def calculate_total(amount, rate):
            return amount * rate
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if operation == 'multiply':
                    if len(args) >= 2:
                        result = decimal_float_service.safe_multiply(args[0], args[1], result_type)
                        return result
                elif operation == 'add':
                    if len(args) >= 2:
                        result = decimal_float_service.safe_add(args[0], args[1], result_type)
                        return result
                elif operation == 'subtract':
                    if len(args) >= 2:
                        result = decimal_float_service.safe_subtract(args[0], args[1], result_type)
                        return result
                elif operation == 'divide':
                    if len(args) >= 2:
                        result = decimal_float_service.safe_divide(args[0], args[1], result_type)
                        return result
                
                # Fallback to original function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in safe_numeric_operation decorator for {func.__name__}: {e}")
                return 0.0 if result_type == 'float' else Decimal('0')
        
        return wrapper
    return decorator 