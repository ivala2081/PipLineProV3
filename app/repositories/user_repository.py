"""
User Repository
Repository pattern implementation for User model
"""
from typing import Optional, List, TYPE_CHECKING
from app.repositories.base_repository import BaseRepository

if TYPE_CHECKING:
    from app.models.user import User


class UserRepository(BaseRepository):
    """Repository for User operations"""
    
    def __init__(self):
        # Lazy import to avoid circular dependency
        from app.models.user import User
        super().__init__(User)
    
    def find_by_username(self, username: str) -> Optional['User']:
        """
        Find user by username
        
        Args:
            username: Username to search for
        
        Returns:
            User instance or None
        """
        return self.find_one_by(username=username)
    
    def find_by_email(self, email: str) -> Optional['User']:
        """
        Find user by email
        
        Args:
            email: Email to search for
        
        Returns:
            User instance or None
        """
        return self.find_one_by(email=email)
    
    def find_active_users(self, organization_id: Optional[int] = None) -> List['User']:
        """
        Find all active users
        
        Args:
            organization_id: Optional organization filter
        
        Returns:
            List of active users
        """
        query = self.query().filter_by(is_active=True)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.all()
    
    def find_by_role(self, role: str, organization_id: Optional[int] = None) -> List['User']:
        """
        Find users by role
        
        Args:
            role: User role
            organization_id: Optional organization filter
        
        Returns:
            List of users with specified role
        """
        query = self.query().filter_by(role=role, is_active=True)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.all()
    
    def find_admins(self, max_level: int = 2) -> List['User']:
        """
        Find admin users
        
        Args:
            max_level: Maximum admin level
        
        Returns:
            List of admin users
        """
        # Lazy import to avoid circular dependency
        from app.models.user import User
        return self.query().filter(
            User.admin_level <= max_level,
            User.is_active == True
        ).all()

