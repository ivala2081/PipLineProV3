"""
File Validation Utility
Validates file uploads using magic numbers (file signatures) for security
"""
import filetype
import logging
from typing import Tuple, Optional, List
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

# Allowed file types with their magic number signatures
ALLOWED_FILE_TYPES = {
    # Images
    'image/png': ['.png'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/gif': ['.gif'],
    
    # Excel files
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    
    # CSV files
    'text/csv': ['.csv'],
    'text/plain': ['.csv'],  # Some CSV files are detected as text/plain
}

# Extension to MIME type mapping for validation
EXTENSION_TO_MIME = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.csv': 'text/csv',
}


def validate_file_content(file_stream, filename: str, allowed_types: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate file content using magic numbers (file signatures)
    
    Args:
        file_stream: File stream to validate
        filename: Original filename (for extension check)
        allowed_types: List of allowed MIME types (defaults to ALLOWED_FILE_TYPES keys)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_types is None:
        allowed_types = list(ALLOWED_FILE_TYPES.keys())
    
    # Reset file stream position
    file_stream.seek(0)
    
    # Read first 261 bytes (enough for most file type detection)
    file_header = file_stream.read(261)
    file_stream.seek(0)  # Reset for actual use
    
    if len(file_header) < 4:
        return False, "File is too small or empty"
    
    # Use filetype library to detect actual file type
    try:
        detected_type = filetype.guess(file_header)
        
        if detected_type is None:
            # For CSV files, filetype might not detect them
            # Check if it's a text file that could be CSV
            if filename.lower().endswith('.csv'):
                # Basic CSV validation: check if it's text
                try:
                    file_header.decode('utf-8')
                    return True, None
                except UnicodeDecodeError:
                    return False, "Invalid CSV file: not a valid text file"
            
            return False, "Unable to detect file type. File may be corrupted or invalid."
        
        detected_mime = detected_type.mime
        
        # Check if detected type is in allowed types
        if detected_mime not in allowed_types:
            return False, f"File type '{detected_mime}' is not allowed. Detected file type does not match extension."
        
        # Verify extension matches detected type
        file_ext = '.' + filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        expected_mimes = EXTENSION_TO_MIME.get(file_ext, [])
        
        if file_ext and file_ext in EXTENSION_TO_MIME:
            expected_mime = EXTENSION_TO_MIME[file_ext]
            if detected_mime != expected_mime:
                # Special case: CSV files can be detected as text/plain
                if file_ext == '.csv' and detected_mime == 'text/plain':
                    return True, None
                return False, f"File extension '{file_ext}' does not match detected file type '{detected_mime}'. Possible file type mismatch."
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating file content: {str(e)}")
        return False, f"Error validating file: {str(e)}"


def validate_file_upload(file, allowed_extensions: Optional[List[str]] = None, 
                        allowed_mime_types: Optional[List[str]] = None,
                        max_size: Optional[int] = None,
                        file_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive file upload validation
    
    Args:
        file: Flask file upload object
        allowed_extensions: List of allowed extensions (e.g., ['.png', '.jpg'])
        allowed_mime_types: List of allowed MIME types
        max_size: Maximum file size in bytes
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check file size - use type-specific limit if available
    if max_size is None and file_type:
        from flask import current_app
        type_limits = current_app.config.get('MAX_FILE_SIZE_BY_TYPE', {})
        max_size = type_limits.get(file_type)
    
    if max_size:
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size ({size_mb:.1f}MB) for this file type"
    
    # Check extension
    if allowed_extensions:
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return False, f"File extension '{file_ext}' is not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
    
    # Validate file content using magic numbers
    is_valid, error_msg = validate_file_content(file.stream, file.filename, allowed_mime_types)
    if not is_valid:
        return False, error_msg
    
    # Validate filename security
    secure_name = secure_filename(file.filename)
    if secure_name != file.filename:
        logger.warning(f"Filename sanitized: {file.filename} -> {secure_name}")
    
    return True, None

