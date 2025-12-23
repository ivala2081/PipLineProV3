"""
Import API endpoints for PipLinePro
Handles Excel file imports for transactions
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import limiter
from app.services.data_import_service import DataImportService
from app.utils.unified_error_handler import handle_api_errors
from app.utils.permission_decorators import require_any_admin

logger = logging.getLogger(__name__)

# Create blueprint
import_bp = Blueprint('import', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@import_bp.route('/preview', methods=['POST'])
@limiter.limit("10 per minute, 50 per hour")  # Rate limiting for file operations
@login_required
@require_any_admin
@handle_api_errors
def preview_import():
    """Preview Excel file before import"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed'
            }), 400
        
        # Validate file content using magic numbers
        from app.utils.file_validation import validate_file_upload
        allowed_extensions = ['.xlsx', '.xls']
        allowed_mime_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]
        # Use type-specific limit for Excel files
        max_size = current_app.config.get('MAX_FILE_SIZE_BY_TYPE', {}).get('excel') or \
                   current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)
        
        is_valid, error_msg = validate_file_upload(
            file,
            allowed_extensions=allowed_extensions,
            allowed_mime_types=allowed_mime_types,
            max_size=max_size,
            file_type='excel'
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'File validation failed: {error_msg}'
            }), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(temp_path)
        
        try:
            # Get preview
            import_service = DataImportService()
            preview_data = import_service.get_import_preview(temp_path)
            
            return jsonify({
                'success': True,
                'message': 'File preview generated successfully',
                'data': preview_data
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error in preview import: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating preview: {str(e)}'
        }), 500

@import_bp.route('/execute', methods=['POST'])
@limiter.limit("5 per minute, 20 per hour")  # Stricter rate limiting for bulk imports
@login_required
@require_any_admin
@handle_api_errors
def execute_import():
    """Execute the actual import"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed'
            }), 400
        
        # Validate file content using magic numbers
        from app.utils.file_validation import validate_file_upload
        allowed_extensions = ['.xlsx', '.xls']
        allowed_mime_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]
        # Use type-specific limit for Excel files
        max_size = current_app.config.get('MAX_FILE_SIZE_BY_TYPE', {}).get('excel') or \
                   current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)
        
        is_valid, error_msg = validate_file_upload(
            file,
            allowed_extensions=allowed_extensions,
            allowed_mime_types=allowed_mime_types,
            max_size=max_size,
            file_type='excel'
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'File validation failed: {error_msg}'
            }), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(temp_path)
        
        try:
            # Execute import
            import_service = DataImportService()
            import_stats = import_service.import_transactions(temp_path, current_user.id)
            
            return jsonify({
                'success': True,
                'message': 'Import completed successfully',
                'data': {
                    'total_rows': import_stats['total_rows'],
                    'successful_imports': import_stats['successful_imports'],
                    'failed_imports': import_stats['failed_imports'],
                    'errors': import_stats['errors'][:10]  # Limit errors to first 10
                }
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error in execute import: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Import failed: {str(e)}'
        }), 500

@import_bp.route('/template', methods=['GET'])
@login_required
@require_any_admin
@handle_api_errors
def get_import_template():
    """Get import template structure"""
    try:
        template_structure = {
            'columns': [
                'AD SOYAD',
                'ÖDEME ŞEKLİ',
                'ŞİRKET',
                'TARİH',
                'KATEGORİ',
                'TUTAR',
                'KOMİSYON',
                'NET',
                'PARA BİRİMİ',
                'KASA'
            ],
            'required_columns': ['AD SOYAD', 'TARİH', 'TUTAR'],
            'date_format': 'DD.MM.YYYY',
            'currency_options': ['TL', 'USD', 'EUR'],
            'category_options': ['YATIRIM', 'ROI', 'ÇEKME'],
            'psp_options': ['#61 CRYPPAY', '#60 CASHPAY', 'SİPAY', 'KUYUMCU', 'TETHER'],
            'business_rules': [
                'WDs (ÇEKME) have no commission',
                'Tether is always treated as USD',
                'USD rate is set to 1 for easy editing',
                'PSP rates are set to 0 initially'
            ]
        }
        
        return jsonify({
            'success': True,
            'data': template_structure
        })
        
    except Exception as e:
        logger.error(f"Error getting import template: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting template: {str(e)}'
        }), 500
