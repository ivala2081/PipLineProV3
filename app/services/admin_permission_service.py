"""
Admin Permission Service for PipLine Treasury System
Manages section permissions for different admin levels
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from app import db
from app.models.config import AdminSectionPermission
from app.models.user import User

logger = logging.getLogger(__name__)

class AdminPermissionService:
    """Service to manage admin section permissions"""
    
    def __init__(self):
        self.default_sections = [
            {
                'section_name': 'dashboard',
                'section_display_name': 'Dashboard',
                'section_description': 'Main dashboard with overview and statistics',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': True
            },
            {
                'section_name': 'transactions',
                'section_display_name': 'Transactions',
                'section_description': 'Manage financial transactions and records',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': True
            },
            {
                'section_name': 'analytics',
                'section_display_name': 'Analytics',
                'section_description': 'Business analytics and reporting',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'clients',
                'section_display_name': 'Clients',
                'section_description': 'Client management and overview',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'psp_track',
                'section_display_name': 'PSP Tracking',
                'section_description': 'Payment Service Provider tracking',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'admin_management',
                'section_display_name': 'Admin Management',
                'section_description': 'Manage administrator accounts and permissions',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'settings',
                'section_display_name': 'Settings',
                'section_description': 'System settings and configuration',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'dropdown_management',
                'section_display_name': 'Dropdown Management',
                'section_description': 'Manage form dropdown options',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'exchange_rates',
                'section_display_name': 'Exchange Rates',
                'section_description': 'Manage currency exchange rates',
                'main_admin_access': True,
                'secondary_admin_access': True,
                'sub_admin_access': False
            },
            {
                'section_name': 'backup_restore',
                'section_display_name': 'Backup & Restore',
                'section_description': 'System backup and restore operations',
                'main_admin_access': True,
                'secondary_admin_access': False,
                'sub_admin_access': False
            },
            {
                'section_name': 'audit_logs',
                'section_display_name': 'Audit Logs',
                'section_description': 'View system audit logs and security events',
                'main_admin_access': True,
                'secondary_admin_access': False,
                'sub_admin_access': False
            },
            {
                'section_name': 'system_config',
                'section_display_name': 'System Configuration',
                'section_description': 'Advanced system configuration options',
                'main_admin_access': True,
                'secondary_admin_access': False,
                'sub_admin_access': False
            },
            {
                'section_name': 'database_management',
                'section_display_name': 'Database Management',
                'section_description': 'Database operations and maintenance',
                'main_admin_access': True,
                'secondary_admin_access': False,
                'sub_admin_access': False
            }
        ]
    
    def initialize_default_sections(self):
        """Initialize default section permissions if they don't exist"""
        try:
            # Create tables if they don't exist
            db.create_all()
            
            for section_data in self.default_sections:
                existing = AdminSectionPermission.query.filter_by(
                    section_name=section_data['section_name']
                ).first()
                
                if not existing:
                    section = AdminSectionPermission(**section_data)
                    db.session.add(section)
                    logger.info(f"Created default section permission: {section_data['section_name']}")
            
            db.session.commit()
            logger.info("Default section permissions initialized successfully")
            return True
            
        except Exception as e:
            try:
                db.session.rollback()
            except:
                pass
            logger.error(f"Error initializing default sections: {e}")
            return False
    
    def get_all_sections(self) -> List[Dict[str, Any]]:
        """Get all section permissions"""
        try:
            sections = AdminSectionPermission.query.filter_by(is_active=True).order_by(
                AdminSectionPermission.section_display_name
            ).all()
            
            return [section.to_dict() for section in sections]
            
        except Exception as e:
            logger.error(f"Error getting all sections: {e}")
            return []
    
    def get_sections_for_admin_level(self, admin_level: int) -> List[Dict[str, Any]]:
        """Get sections accessible for specific admin level"""
        try:
            sections = AdminSectionPermission.query.filter_by(is_active=True).all()
            
            accessible_sections = []
            for section in sections:
                if section.has_access_for_level(admin_level):
                    accessible_sections.append(section.to_dict())
            
            return accessible_sections
            
        except Exception as e:
            logger.error(f"Error getting sections for admin level {admin_level}: {e}")
            return []
    
    def can_access_section(self, admin_level: int, section_name: str) -> bool:
        """Check if admin level can access specific section"""
        try:
            section = AdminSectionPermission.query.filter_by(
                section_name=section_name,
                is_active=True
            ).first()
            
            if not section:
                # If section doesn't exist in permissions, default to main admin only
                return admin_level == 1
            
            return section.has_access_for_level(admin_level)
            
        except Exception as e:
            logger.error(f"Error checking section access: {e}")
            return False
    
    def update_section_permissions(self, section_id: int, permissions: Dict[str, bool]) -> bool:
        """Update section permissions"""
        try:
            section = AdminSectionPermission.query.get(section_id)
            if not section:
                logger.error(f"Section with ID {section_id} not found")
                return False
            
            # Update permissions
            if 'main_admin_access' in permissions:
                section.main_admin_access = permissions['main_admin_access']
            if 'secondary_admin_access' in permissions:
                section.secondary_admin_access = permissions['secondary_admin_access']
            if 'sub_admin_access' in permissions:
                section.sub_admin_access = permissions['sub_admin_access']
            
            section.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Updated permissions for section: {section.section_name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating section permissions: {e}")
            return False
    
    def update_multiple_sections(self, section_permissions: List[Dict[str, Any]]) -> bool:
        """Update multiple section permissions at once"""
        try:
            for section_data in section_permissions:
                section_id = section_data.get('id')
                permissions = section_data.get('permissions', {})
                
                if section_id and permissions:
                    self.update_section_permissions(section_id, permissions)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating multiple sections: {e}")
            return False
    
    def get_section_by_name(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Get section by name"""
        try:
            section = AdminSectionPermission.query.filter_by(
                section_name=section_name,
                is_active=True
            ).first()
            
            return section.to_dict() if section else None
            
        except Exception as e:
            logger.error(f"Error getting section by name: {e}")
            return None
    
    def create_custom_section(self, section_data: Dict[str, Any]) -> bool:
        """Create a custom section permission"""
        try:
            section = AdminSectionPermission(**section_data)
            db.session.add(section)
            db.session.commit()
            
            logger.info(f"Created custom section: {section_data['section_name']}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating custom section: {e}")
            return False
    
    def delete_section(self, section_id: int) -> bool:
        """Delete a section permission (soft delete)"""
        try:
            section = AdminSectionPermission.query.get(section_id)
            if not section:
                logger.error(f"Section with ID {section_id} not found")
                return False
            
            section.is_active = False
            section.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Deleted section: {section.section_name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting section: {e}")
            return False
    
    def get_accessible_sections_for_user(self, user: User) -> List[str]:
        """Get list of accessible section names for a user"""
        try:
            if not user.is_any_admin():
                return ['dashboard']  # Regular users only see dashboard
            
            sections = self.get_sections_for_admin_level(user.admin_level)
            return [section['section_name'] for section in sections]
            
        except Exception as e:
            logger.error(f"Error getting accessible sections for user: {e}")
            return ['dashboard']

# Create global instance
admin_permission_service = AdminPermissionService() 