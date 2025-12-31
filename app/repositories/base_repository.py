"""
Base Repository Pattern Implementation
Provides a consistent interface for data access

This base repository provides common CRUD operations that can be extended
by specific repository implementations. It follows the Repository Pattern
to separate data access logic from business logic.
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Query
from app import db
from app.utils.type_hints_helper import OptionalInt

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialize repository with a model class
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID
        
        Args:
            id: Entity ID
        
        Returns:
            Entity instance or None
        """
        return self.model.query.get(id)
    
    def get_all(self, limit: OptionalInt = None, offset: int = 0) -> List[T]:
        """
        Get all entities
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
        
        Returns:
            List of entities
        """
        query = self.model.query
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def find_by(self, **kwargs) -> List[T]:
        """
        Find entities by criteria
        
        Args:
            **kwargs: Filter criteria
        
        Returns:
            List of matching entities
        """
        return self.model.query.filter_by(**kwargs).all()
    
    def find_one_by(self, **kwargs) -> Optional[T]:
        """
        Find single entity by criteria
        
        Args:
            **kwargs: Filter criteria
        
        Returns:
            Entity instance or None
        """
        return self.model.query.filter_by(**kwargs).first()
    
    def create(self, **kwargs) -> T:
        """
        Create new entity
        
        Args:
            **kwargs: Entity attributes
        
        Returns:
            Created entity instance
        """
        entity = self.model(**kwargs)
        db.session.add(entity)
        db.session.commit()
        return entity
    
    def update(self, entity: T, **kwargs) -> T:
        """
        Update entity
        
        Args:
            entity: Entity instance to update
            **kwargs: Attributes to update
        
        Returns:
            Updated entity instance
        """
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        db.session.commit()
        return entity
    
    def delete(self, entity: T) -> bool:
        """
        Delete entity
        
        Args:
            entity: Entity instance to delete
        
        Returns:
            True if deleted successfully
        """
        try:
            db.session.delete(entity)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def delete_by_id(self, id: int) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
        
        Returns:
            True if deleted successfully
        """
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False
    
    def count(self, **kwargs) -> int:
        """
        Count entities matching criteria
        
        Args:
            **kwargs: Filter criteria
        
        Returns:
            Count of matching entities
        """
        if kwargs:
            return self.model.query.filter_by(**kwargs).count()
        return self.model.query.count()
    
    def exists(self, **kwargs) -> bool:
        """
        Check if entity exists
        
        Args:
            **kwargs: Filter criteria
        
        Returns:
            True if entity exists
        """
        return self.model.query.filter_by(**kwargs).first() is not None
    
    def query(self) -> Query:
        """
        Get base query object for custom queries
        
        Returns:
            SQLAlchemy Query object
        """
        return self.model.query
