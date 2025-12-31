"""
Docstring Template and Guidelines
Standard format for function and class docstrings
"""

# Function docstring template
FUNCTION_DOCSTRING_TEMPLATE = '''
    """
    Brief one-line description of what the function does.
    
    More detailed explanation if needed. Can span multiple lines.
    Explain the purpose, behavior, and any important details.
    
    Args:
        param1 (type): Description of param1
        param2 (type, optional): Description of param2. Defaults to None.
        **kwargs: Additional keyword arguments
    
    Returns:
        type: Description of return value
    
    Raises:
        ValueError: When invalid input is provided
        KeyError: When required key is missing
    
    Example:
        >>> result = function_name('value1', param2='value2')
        >>> print(result)
        'output'
    
    Note:
        Any additional notes or warnings
    """
'''

# Class docstring template
CLASS_DOCSTRING_TEMPLATE = '''
    """
    Brief one-line description of the class.
    
    More detailed explanation of the class purpose, behavior, and usage.
    Explain the main responsibilities and how it fits into the system.
    
    Attributes:
        attr1 (type): Description of attr1
        attr2 (type): Description of attr2
    
    Example:
        >>> instance = MyClass(param1='value')
        >>> instance.method()
        'result'
    
    Note:
        Any additional notes or implementation details
    """
'''

# Module docstring template
MODULE_DOCSTRING_TEMPLATE = '''
"""
Module Name
Brief description of the module's purpose.

This module provides [main functionality]. It handles [key responsibilities]
and integrates with [other modules/services].

Key Classes:
    - ClassName: Description
    - AnotherClass: Description

Key Functions:
    - function_name: Description
    - another_function: Description

Example:
    Basic usage example here

Note:
    Any important notes about the module
"""
'''

