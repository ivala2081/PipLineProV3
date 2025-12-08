"""
Base Repository Pattern
Provides common database operations for all models
"""
import logging
from typing import List, Optional, Dict, Any, Type, TypeVar
from sqlalchemy.orm import Query, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app import db

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[T]):
        """
        Initialize repository with a model class
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self.session = db.session
    
    def get_by_id(self, id: int, eager_load: List[str] = None) -> Optional[T]:
        """
        Get a single record by ID with optional eager loading
        
        Args:
            id: Record ID
            eager_load: List of relationship names to eager load
            
        Returns:
            Model instance or None
        """
        try:
            query = self.session.query(self.model)
            
            # Add eager loading if specified
            if eager_load:
                for relationship in eager_load:
                    query = query.options(joinedload(getattr(self.model, relationship)))
            
            return query.filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {e}")
            return None
    
    def get_all(self, filters: Dict[str, Any] = None, eager_load: List[str] = None,
                order_by=None, limit: int = None, offset: int = None) -> List[T]:
        """
        Get all records with optional filtering, eager loading, and pagination
        
        Args:
            filters: Dictionary of field: value pairs for filtering
            eager_load: List of relationship names to eager load
            order_by: Column to order by
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        try:
            query = self.session.query(self.model)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
            
            # Add eager loading
            if eager_load:
                for relationship in eager_load:
                    if hasattr(self.model, relationship):
                        query = query.options(joinedload(getattr(self.model, relationship)))
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []
    
    def create(self, **kwargs) -> Optional[T]:
        """
        Create a new record
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance or None
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.commit()
            logger.info(f"Created {self.model.__name__} with ID {instance.id}")
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            return None
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update an existing record
        
        Args:
            id: Record ID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.commit()
            logger.info(f"Updated {self.model.__name__} with ID {id}")
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            return None
    
    def delete(self, id: int) -> bool:
        """
        Delete a record
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            logger.info(f"Deleted {self.model.__name__} with ID {id}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            return False
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filtering
        
        Args:
            filters: Dictionary of field: value pairs for filtering
            
        Returns:
            Count of matching records
        """
        try:
            query = self.session.query(self.model)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    def paginate(self, page: int = 1, per_page: int = 50, filters: Dict[str, Any] = None,
                 eager_load: List[str] = None, order_by=None) -> Dict[str, Any]:
        """
        Paginate records with filtering and eager loading
        
        Args:
            page: Page number (1-indexed)
            per_page: Records per page
            filters: Dictionary of field: value pairs for filtering
            eager_load: List of relationship names to eager load
            order_by: Column to order by
            
        Returns:
            Dictionary with items and pagination info
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count
            total = self.count(filters)
            
            # Get paginated items
            items = self.get_all(
                filters=filters,
                eager_load=eager_load,
                order_by=order_by,
                limit=per_page,
                offset=offset
            )
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            
            return {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
            }
        except SQLAlchemyError as e:
            logger.error(f"Error paginating {self.model.__name__}: {e}")
            return {
                'items': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            }

