"""
Audit Service for Admin Actions
Centralized logging of sensitive administrative operations
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from flask import request, has_request_context
from flask_login import current_user

from app import db
from app.models.audit import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging administrative actions"""
    
    # Admin action types
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    
    # Admin-specific actions
    ACTION_ADMIN_CREATE = 'ADMIN_CREATE'
    ACTION_ADMIN_UPDATE = 'ADMIN_UPDATE'
    ACTION_ADMIN_DELETE = 'ADMIN_DELETE'
    ACTION_ADMIN_PERMISSION_CHANGE = 'ADMIN_PERMISSION_CHANGE'
    ACTION_ADMIN_LEVEL_CHANGE = 'ADMIN_LEVEL_CHANGE'
    ACTION_ADMIN_ACTIVATE = 'ADMIN_ACTIVATE'
    ACTION_ADMIN_DEACTIVATE = 'ADMIN_DEACTIVATE'
    ACTION_USER_PASSWORD_CHANGE = 'USER_PASSWORD_CHANGE'
    ACTION_USER_ACCOUNT_LOCK = 'USER_ACCOUNT_LOCK'
    ACTION_USER_ACCOUNT_UNLOCK = 'USER_ACCOUNT_UNLOCK'
    ACTION_SYSTEM_CONFIG_CHANGE = 'SYSTEM_CONFIG_CHANGE'
    ACTION_BACKUP_CREATE = 'BACKUP_CREATE'
    ACTION_BACKUP_RESTORE = 'BACKUP_RESTORE'
    ACTION_DATABASE_OPERATION = 'DATABASE_OPERATION'
    ACTION_BULK_DELETE = 'BULK_DELETE'
    ACTION_IMPORT_DATA = 'IMPORT_DATA'
    ACTION_EXPORT_DATA = 'EXPORT_DATA'
    
    @staticmethod
    def get_ip_address() -> Optional[str]:
        """Get client IP address from request"""
        if not has_request_context():
            return None
        # Try to get real IP (considering proxies)
        return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    @staticmethod
    def log_admin_action(
        action: str,
        table_name: str,
        record_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Optional[AuditLog]:
        """
        Log an administrative action
        
        Args:
            action: Action type (e.g., 'ADMIN_CREATE', 'USER_PASSWORD_CHANGE')
            table_name: Name of the table/entity being modified
            record_id: ID of the record being modified
            old_values: Previous values (for UPDATE actions)
            new_values: New values (for CREATE/UPDATE actions)
            additional_info: Additional context information
            user_id: User performing the action (defaults to current_user)
        
        Returns:
            AuditLog instance if successful, None otherwise
        """
        try:
            # Get user ID
            if user_id is None:
                if not current_user.is_authenticated:
                    logger.warning("Cannot log admin action: user not authenticated")
                    return None
                user_id = current_user.id
            
            # Prepare values for JSON storage
            old_values_json = json.dumps(old_values) if old_values else None
            new_values_json = json.dumps(new_values) if new_values else None
            
            # Add additional info to new_values if provided
            if additional_info:
                info_dict = new_values.copy() if new_values else {}
                info_dict['_audit_info'] = additional_info
                new_values_json = json.dumps(info_dict)
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_values=old_values_json,
                new_values=new_values_json,
                ip_address=AuditService.get_ip_address(),
                timestamp=datetime.now(timezone.utc)
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"Audit log created: {action} on {table_name}:{record_id} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_user_management_action(
        action: str,
        target_user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """Log user/admin management actions"""
        return AuditService.log_admin_action(
            action=action,
            table_name='user',
            record_id=target_user_id,
            old_values=old_values,
            new_values=new_values,
            additional_info={
                'target_username': User.query.get(target_user_id).username if User.query.get(target_user_id) else 'Unknown'
            }
        )
    
    @staticmethod
    def log_admin_creation(target_admin: User) -> Optional[AuditLog]:
        """Log admin account creation"""
        return AuditService.log_user_management_action(
            action=AuditService.ACTION_ADMIN_CREATE,
            target_user_id=target_admin.id,
            new_values={
                'username': target_admin.username,
                'admin_level': target_admin.admin_level,
                'role': target_admin.role,
                'permissions': target_admin.admin_permissions,
                'created_by': target_admin.created_by
            }
        )
    
    @staticmethod
    def log_admin_update(target_admin: User, old_values: Dict[str, Any]) -> Optional[AuditLog]:
        """Log admin account modification"""
        new_values = {
            'username': target_admin.username,
            'admin_level': target_admin.admin_level,
            'role': target_admin.role,
            'is_active': target_admin.is_active,
            'permissions': target_admin.admin_permissions
        }
        return AuditService.log_user_management_action(
            action=AuditService.ACTION_ADMIN_UPDATE,
            target_user_id=target_admin.id,
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def log_admin_deletion(target_admin: User) -> Optional[AuditLog]:
        """Log admin account deletion"""
        return AuditService.log_user_management_action(
            action=AuditService.ACTION_ADMIN_DELETE,
            target_user_id=target_admin.id,
            old_values={
                'username': target_admin.username,
                'admin_level': target_admin.admin_level,
                'role': target_admin.role
            }
        )
    
    @staticmethod
    def log_admin_level_change(target_admin: User, old_level: int, new_level: int) -> Optional[AuditLog]:
        """Log admin level change"""
        return AuditService.log_user_management_action(
            action=AuditService.ACTION_ADMIN_LEVEL_CHANGE,
            target_user_id=target_admin.id,
            old_values={'admin_level': old_level},
            new_values={'admin_level': new_level},
            additional_info={
                'old_level_name': User(id=0, admin_level=old_level).get_admin_title(),
                'new_level_name': User(id=0, admin_level=new_level).get_admin_title()
            }
        )
    
    @staticmethod
    def log_permission_change(target_admin: User, old_permissions: Dict[str, Any], new_permissions: Dict[str, Any]) -> Optional[AuditLog]:
        """Log admin permission changes"""
        return AuditService.log_user_management_action(
            action=AuditService.ACTION_ADMIN_PERMISSION_CHANGE,
            target_user_id=target_admin.id,
            old_values={'permissions': old_permissions},
            new_values={'permissions': new_permissions}
        )
    
    @staticmethod
    def log_admin_status_change(target_admin: User, is_active: bool) -> Optional[AuditLog]:
        """Log admin activation/deactivation"""
        action = AuditService.ACTION_ADMIN_ACTIVATE if is_active else AuditService.ACTION_ADMIN_DEACTIVATE
        return AuditService.log_user_management_action(
            action=action,
            target_user_id=target_admin.id,
            old_values={'is_active': not is_active},
            new_values={'is_active': is_active}
        )
    
    @staticmethod
    def log_system_config_change(config_key: str, old_value: Any, new_value: Any) -> Optional[AuditLog]:
        """Log system configuration changes"""
        return AuditService.log_admin_action(
            action=AuditService.ACTION_SYSTEM_CONFIG_CHANGE,
            table_name='config',
            record_id=0,  # No specific record ID for config
            old_values={config_key: str(old_value)},
            new_values={config_key: str(new_value)},
            additional_info={'config_key': config_key}
        )
    
    @staticmethod
    def log_backup_operation(action: str, backup_file: str, success: bool) -> Optional[AuditLog]:
        """Log backup/restore operations"""
        return AuditService.log_admin_action(
            action=action,
            table_name='backup',
            record_id=0,
            new_values={
                'backup_file': backup_file,
                'success': success
            }
        )
    
    @staticmethod
    def log_database_operation(operation: str, details: Dict[str, Any]) -> Optional[AuditLog]:
        """Log database operations (migrations, vacuum, etc.)"""
        return AuditService.log_admin_action(
            action=AuditService.ACTION_DATABASE_OPERATION,
            table_name='database',
            record_id=0,
            new_values={
                'operation': operation,
                **details
            }
        )
    
    @staticmethod
    def log_bulk_operation(action: str, table_name: str, affected_count: int, criteria: Dict[str, Any]) -> Optional[AuditLog]:
        """Log bulk operations (bulk delete, bulk update, etc.)"""
        return AuditService.log_admin_action(
            action=action,
            table_name=table_name,
            record_id=0,  # Bulk operations affect multiple records
            new_values={
                'affected_count': affected_count,
                'criteria': criteria
            }
        )
    
    @staticmethod
    def get_recent_admin_actions(user_id: Optional[int] = None, limit: int = 100) -> list:
        """Get recent admin actions"""
        query = AuditLog.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        # Filter to admin-related actions
        admin_actions = [
            AuditService.ACTION_ADMIN_CREATE,
            AuditService.ACTION_ADMIN_UPDATE,
            AuditService.ACTION_ADMIN_DELETE,
            AuditService.ACTION_ADMIN_PERMISSION_CHANGE,
            AuditService.ACTION_ADMIN_LEVEL_CHANGE,
            AuditService.ACTION_ADMIN_ACTIVATE,
            AuditService.ACTION_ADMIN_DEACTIVATE,
            AuditService.ACTION_USER_PASSWORD_CHANGE,
            AuditService.ACTION_USER_ACCOUNT_LOCK,
            AuditService.ACTION_SYSTEM_CONFIG_CHANGE,
            AuditService.ACTION_BACKUP_CREATE,
            AuditService.ACTION_BACKUP_RESTORE,
            AuditService.ACTION_DATABASE_OPERATION,
            AuditService.ACTION_BULK_DELETE
        ]
        
        query = query.filter(AuditLog.action.in_(admin_actions))
        query = query.order_by(AuditLog.timestamp.desc())
        
        return query.limit(limit).all()


# Singleton instance
audit_service = AuditService()

