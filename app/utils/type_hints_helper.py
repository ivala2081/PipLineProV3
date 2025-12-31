"""
Type hints helper utilities
Provides common type aliases and helpers for type hints
"""
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, date
from decimal import Decimal
from flask import Response
from sqlalchemy.orm import Query

# Common type aliases
JsonDict = Dict[str, Any]
JsonList = List[JsonDict]
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalFloat = Optional[float]
OptionalDecimal = Optional[Decimal]
OptionalDate = Optional[date]
OptionalDateTime = Optional[datetime]

# API response types
ApiResponse = Union[Response, Tuple[JsonDict, int]]
SuccessResponse = Tuple[JsonDict, int]
ErrorResponse = Tuple[JsonDict, int]

# Database types
DbQuery = Query
DbModel = Any  # SQLAlchemy model base

# Pagination types
PaginationResult = Dict[str, Any]
PageNumber = int
PageSize = int

# Cache types
CacheKey = str
CacheValue = Any
CacheTTL = int

# Validation types
ValidationResult = Dict[str, Any]
ValidationError = Dict[str, str]

