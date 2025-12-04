"""
Pydantic models for API validation
"""
from pydantic import BaseModel, field_validator, Field
from decimal import Decimal
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class CurrencyEnum(str, Enum):
    TL = "TL"
    USD = "USD"
    EUR = "EUR"

class CategoryEnum(str, Enum):
    WD = "WD"
    DEP = "DEP"

class TransactionCreate(BaseModel):
    """Model for creating a new transaction"""
    client_name: str = Field(..., min_length=1, max_length=100, description="Client name")
    amount: Decimal = Field(..., gt=0, description="Transaction amount (always positive)")
    commission: Optional[Decimal] = Field(None, ge=0, description="Commission amount")
    currency: CurrencyEnum = Field(CurrencyEnum.TL, description="Currency")
    psp: Optional[str] = Field(None, max_length=50, description="Payment Service Provider")
    category: Optional[CategoryEnum] = Field(None, description="Transaction category (DEP=positive, WD=negative)")
    transaction_date: date = Field(..., description="Transaction date")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @field_validator('client_name')
    @classmethod
    def validate_client_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Client name cannot be empty')
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 999999999.99:
            raise ValueError('Amount too large')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "John Doe",
                "amount": "1000.00",
                "commission": "50.00",
                "currency": "TL",
                "psp": "PayPal",
                "category": "DEP",
                "transaction_date": "2025-01-15",
                "notes": "Monthly deposit"
            }
        }

class TransactionUpdate(BaseModel):
    """Model for updating a transaction"""
    client_name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, description="Transaction amount (always positive)")
    commission: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[CurrencyEnum] = None
    psp: Optional[str] = Field(None, max_length=50)
    category: Optional[CategoryEnum] = None
    transaction_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Amount must be positive')
            if v > 999999999.99:
                raise ValueError('Amount too large')
        return v

class TransactionResponse(BaseModel):
    """Model for transaction response"""
    id: int
    client_name: str
    amount: Decimal
    commission: Decimal
    net_amount: Decimal
    currency: str
    psp: Optional[str]
    category: Optional[str]
    transaction_date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "client_name": "John Doe",
                "amount": "1000.00",
                "commission": "50.00",
                "net_amount": "950.00",
                "currency": "TL",
                "psp": "PayPal",
                "category": "DEP",
                "transaction_date": "2025-01-15",
                "notes": "Monthly deposit",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "created_by": 1
            }
        }

class TransactionFilters(BaseModel):
    """Model for transaction filtering"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    psp: Optional[str] = None
    category: Optional[CategoryEnum] = None
    currency: Optional[CurrencyEnum] = None
    client_name: Optional[str] = None
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    """Model for paginated responses"""
    items: List[TransactionResponse]
    total: int
    page: int
    limit: int
    pages: int
    
    @field_validator('pages', mode='before')
    @classmethod
    def calculate_pages(cls, v, info):
        if 'total' in info.data and 'limit' in info.data:
            return (info.data['total'] + info.data['limit'] - 1) // info.data['limit']
        return v

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str
    detail: Optional[str] = None
    status_code: int = 400
