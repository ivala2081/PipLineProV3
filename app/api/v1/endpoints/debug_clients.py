"""
Debug endpoint for Clients page issues
Comprehensive diagnostics to identify the root cause
"""
import logging
import traceback
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import text, func
from datetime import datetime

from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.organization import Organization

logger = logging.getLogger(__name__)

debug_clients_bp = Blueprint('debug_clients', __name__)

@debug_clients_bp.route('/debug/clients', methods=['GET'])
@login_required
def debug_clients_endpoint():
    """
    Comprehensive debug endpoint for Clients page issues
    Returns detailed diagnostics about what's failing
    """
    diagnostics = {
        'timestamp': datetime.utcnow().isoformat(),
        'endpoint': '/debug/clients',
        'status': 'running',
        'checks': {}
    }
    
    try:
        # Check 1: Current User Info
        diagnostics['checks']['current_user'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            diagnostics['checks']['current_user']['data'] = {
                'id': current_user.id,
                'id_type': type(current_user.id).__name__,
                'username': current_user.username,
                'is_authenticated': current_user.is_authenticated,
                'is_active': current_user.is_active,
                'organization_id': getattr(current_user, 'organization_id', None),
                'organization_id_type': type(getattr(current_user, 'organization_id', None)).__name__,
                'admin_level': getattr(current_user, 'admin_level', None),
            }
            diagnostics['checks']['current_user']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['current_user']['status'] = 'error'
            diagnostics['checks']['current_user']['error'] = str(e)
            diagnostics['checks']['current_user']['traceback'] = traceback.format_exc()
        
        # Check 2: Database Connection
        diagnostics['checks']['database'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            result = db.session.execute(text('SELECT 1')).scalar()
            diagnostics['checks']['database']['data'] = {
                'connected': result == 1,
                'engine': str(db.engine.url),
                'pool_size': db.engine.pool.size if hasattr(db.engine.pool, 'size') else 'N/A'
            }
            diagnostics['checks']['database']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['database']['status'] = 'error'
            diagnostics['checks']['database']['error'] = str(e)
            diagnostics['checks']['database']['traceback'] = traceback.format_exc()
        
        # Check 3: Transaction Table Schema
        diagnostics['checks']['transaction_schema'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            columns = {}
            for column in Transaction.__table__.columns:
                columns[column.name] = {
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key
                }
            diagnostics['checks']['transaction_schema']['data'] = {
                'columns': columns,
                'has_organization_id': 'organization_id' in columns
            }
            diagnostics['checks']['transaction_schema']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['transaction_schema']['status'] = 'error'
            diagnostics['checks']['transaction_schema']['error'] = str(e)
            diagnostics['checks']['transaction_schema']['traceback'] = traceback.format_exc()
        
        # Check 4: Simple Transaction Count (No Filters)
        diagnostics['checks']['transaction_count'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            total_count = db.session.query(func.count(Transaction.id)).scalar()
            diagnostics['checks']['transaction_count']['data'] = {
                'total_transactions': total_count
            }
            diagnostics['checks']['transaction_count']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['transaction_count']['status'] = 'error'
            diagnostics['checks']['transaction_count']['error'] = str(e)
            diagnostics['checks']['transaction_count']['traceback'] = traceback.format_exc()
        
        # Check 5: Clients Query (Basic)
        diagnostics['checks']['clients_basic'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            clients_count = db.session.query(
                func.count(func.distinct(Transaction.client_name))
            ).filter(
                Transaction.client_name.isnot(None),
                Transaction.client_name != ''
            ).scalar()
            
            diagnostics['checks']['clients_basic']['data'] = {
                'unique_clients': clients_count
            }
            diagnostics['checks']['clients_basic']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['clients_basic']['status'] = 'error'
            diagnostics['checks']['clients_basic']['error'] = str(e)
            diagnostics['checks']['clients_basic']['traceback'] = traceback.format_exc()
        
        # Check 6: Clients Query (With Aggregation)
        diagnostics['checks']['clients_aggregation'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            clients_query = db.session.query(
                Transaction.client_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.client_name.isnot(None),
                Transaction.client_name != ''
            ).group_by(Transaction.client_name).limit(5)
            
            clients_sample = []
            for row in clients_query.all():
                clients_sample.append({
                    'client_name': row.client_name,
                    'transaction_count': row.transaction_count,
                    'total_amount': float(row.total_amount) if row.total_amount else 0
                })
            
            diagnostics['checks']['clients_aggregation']['data'] = {
                'sample_clients': clients_sample,
                'sample_count': len(clients_sample)
            }
            diagnostics['checks']['clients_aggregation']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['clients_aggregation']['status'] = 'error'
            diagnostics['checks']['clients_aggregation']['error'] = str(e)
            diagnostics['checks']['clients_aggregation']['traceback'] = traceback.format_exc()
        
        # Check 7: Organization Filter Check
        diagnostics['checks']['organization_filter'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            from flask import g
            diagnostics['checks']['organization_filter']['data'] = {
                'g.organization_id': getattr(g, 'organization_id', 'NOT SET'),
                'g.is_super_admin': getattr(g, 'is_super_admin', 'NOT SET'),
                'g.organization': getattr(g, 'organization', 'NOT SET'),
            }
            diagnostics['checks']['organization_filter']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['organization_filter']['status'] = 'error'
            diagnostics['checks']['organization_filter']['error'] = str(e)
            diagnostics['checks']['organization_filter']['traceback'] = traceback.format_exc()
        
        # Check 8: Test Actual Clients API Query
        diagnostics['checks']['clients_api_simulation'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            # Simulate the actual query from the clients endpoint
            query = db.session.query(
                Transaction.client_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net'),
                func.min(Transaction.date).label('first_transaction'),
                func.max(Transaction.date).label('last_transaction')
            ).filter(
                Transaction.client_name.isnot(None),
                Transaction.client_name != ''
            ).group_by(Transaction.client_name)
            
            # Try to execute
            result_count = query.count()
            first_result = query.first()
            
            diagnostics['checks']['clients_api_simulation']['data'] = {
                'total_clients': result_count,
                'first_client': {
                    'client_name': first_result.client_name if first_result else None,
                    'transaction_count': first_result.transaction_count if first_result else None,
                    'total_amount': float(first_result.total_amount) if first_result and first_result.total_amount else None
                } if first_result else None,
                'query_successful': True
            }
            diagnostics['checks']['clients_api_simulation']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['clients_api_simulation']['status'] = 'error'
            diagnostics['checks']['clients_api_simulation']['error'] = str(e)
            diagnostics['checks']['clients_api_simulation']['traceback'] = traceback.format_exc()
        
        # Check 9: Check for NULL/Invalid organization_id values
        diagnostics['checks']['organization_id_values'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            # Check transactions with organization_id
            org_id_stats = db.session.query(
                Transaction.organization_id,
                func.count(Transaction.id).label('count')
            ).group_by(Transaction.organization_id).all()
            
            org_id_distribution = {}
            for row in org_id_stats:
                key = str(row.organization_id) if row.organization_id is not None else 'NULL'
                org_id_distribution[key] = row.count
            
            diagnostics['checks']['organization_id_values']['data'] = {
                'distribution': org_id_distribution,
                'unique_org_ids': len(org_id_distribution)
            }
            diagnostics['checks']['organization_id_values']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['organization_id_values']['status'] = 'error'
            diagnostics['checks']['organization_id_values']['error'] = str(e)
            diagnostics['checks']['organization_id_values']['traceback'] = traceback.format_exc()
        
        # Check 10: Test the actual /clients endpoint
        diagnostics['checks']['actual_clients_endpoint'] = {
            'status': 'checking',
            'data': {}
        }
        try:
            from app.api.v1.endpoints.transactions import get_clients
            # Note: We can't actually call it here, but we can check if it's importable
            diagnostics['checks']['actual_clients_endpoint']['data'] = {
                'endpoint_importable': True,
                'endpoint_name': get_clients.__name__
            }
            diagnostics['checks']['actual_clients_endpoint']['status'] = 'ok'
        except Exception as e:
            diagnostics['checks']['actual_clients_endpoint']['status'] = 'error'
            diagnostics['checks']['actual_clients_endpoint']['error'] = str(e)
            diagnostics['checks']['actual_clients_endpoint']['traceback'] = traceback.format_exc()
        
        # Overall Status
        failed_checks = [k for k, v in diagnostics['checks'].items() if v['status'] == 'error']
        if failed_checks:
            diagnostics['status'] = 'failed'
            diagnostics['failed_checks'] = failed_checks
            diagnostics['summary'] = f"{len(failed_checks)} checks failed: {', '.join(failed_checks)}"
        else:
            diagnostics['status'] = 'success'
            diagnostics['summary'] = 'All checks passed'
        
        return jsonify(diagnostics), 200
        
    except Exception as e:
        diagnostics['status'] = 'critical_error'
        diagnostics['error'] = str(e)
        diagnostics['traceback'] = traceback.format_exc()
        return jsonify(diagnostics), 500

