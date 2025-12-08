from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.translation_service import TranslationService
from app.models.translation import (
    TranslationKey, Translation, CustomDictionary, 
    TranslationMemory, TranslationLog, TranslationSettings
)
from app import db
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

translations_bp = Blueprint('translations', __name__)
translation_service = TranslationService()


@translations_bp.route('/keys', methods=['GET'])
@login_required
def get_translation_keys():
    """Get all translation keys with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        context = request.args.get('context')
        search = request.args.get('search')
        
        query = TranslationKey.query.filter_by(is_active=True)
        
        if context:
            query = query.filter_by(context=context)
        
        if search:
            query = query.filter(TranslationKey.key_path.contains(search))
        
        keys = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [{
                'id': key.id,
                'key_path': key.key_path,
                'description': key.description,
                'context': key.context,
                'created_at': key.created_at.isoformat(),
                'updated_at': key.updated_at.isoformat()
            } for key in keys.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': keys.total,
                'pages': keys.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting translation keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/keys', methods=['POST'])
@login_required
def add_translation_key():
    """Add a new translation key"""
    try:
        data = request.get_json()
        key_path = data.get('key_path')
        description = data.get('description')
        context = data.get('context')
        
        if not key_path:
            return jsonify({'success': False, 'error': 'key_path is required'}), 400
        
        key = translation_service.add_translation_key(key_path, description, context)
        
        return jsonify({
            'success': True,
            'data': {
                'id': key.id,
                'key_path': key.key_path,
                'description': key.description,
                'context': key.context,
                'created_at': key.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding translation key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/translations', methods=['GET'])
@login_required
def get_translations():
    """Get translations with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        language = request.args.get('language')
        key_path = request.args.get('key_path')
        is_approved = request.args.get('is_approved', type=bool)
        
        query = db.session.query(Translation, TranslationKey).join(
            TranslationKey, Translation.key_id == TranslationKey.id
        ).filter(TranslationKey.is_active == True)
        
        if language:
            query = query.filter(Translation.language_code == language)
        
        if key_path:
            query = query.filter(TranslationKey.key_path.contains(key_path))
        
        if is_approved is not None:
            query = query.filter(Translation.is_approved == is_approved)
        
        translations = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [{
                'id': trans.id,
                'key_path': key.key_path,
                'language_code': trans.language_code,
                'translation_text': trans.translation_text,
                'is_approved': trans.is_approved,
                'is_auto_translated': trans.is_auto_translated,
                'confidence_score': trans.confidence_score,
                'created_at': trans.created_at.isoformat(),
                'updated_at': trans.updated_at.isoformat()
            } for trans, key in translations.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': translations.total,
                'pages': translations.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting translations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/translations', methods=['POST'])
@login_required
def add_translation():
    """Add or update a translation"""
    try:
        data = request.get_json()
        key_path = data.get('key_path')
        language = data.get('language')
        text = data.get('text')
        is_approved = data.get('is_approved', False)
        
        if not all([key_path, language, text]):
            return jsonify({'success': False, 'error': 'key_path, language, and text are required'}), 400
        
        translation = translation_service.add_translation(
            key_path, language, text, is_approved
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': translation.id,
                'key_path': key_path,
                'language_code': translation.language_code,
                'translation_text': translation.translation_text,
                'is_approved': translation.is_approved,
                'is_auto_translated': translation.is_auto_translated,
                'confidence_score': translation.confidence_score,
                'created_at': translation.created_at.isoformat(),
                'updated_at': translation.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding translation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/auto-translate', methods=['POST'])
@login_required
def auto_translate():
    """Auto translate a key"""
    try:
        data = request.get_json()
        key_path = data.get('key_path')
        target_language = data.get('target_language')
        source_language = data.get('source_language')
        
        if not all([key_path, target_language]):
            return jsonify({'success': False, 'error': 'key_path and target_language are required'}), 400
        
        translated_text = translation_service.auto_translate(key_path, target_language, source_language)
        
        if translated_text:
            return jsonify({
                'success': True,
                'data': {
                    'key_path': key_path,
                    'target_language': target_language,
                    'translated_text': translated_text
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not auto-translate this key'
            }), 400
        
    except Exception as e:
        logger.error(f"Error auto translating: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/bulk-translate', methods=['POST'])
@login_required
def bulk_translate():
    """Bulk translate multiple keys"""
    try:
        data = request.get_json()
        translations = data.get('translations', [])
        
        if not translations:
            return jsonify({'success': False, 'error': 'translations array is required'}), 400
        
        results = translation_service.bulk_translate(translations)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error bulk translating: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/custom-dictionary', methods=['GET'])
@login_required
def get_custom_dictionary():
    """Get custom dictionary entries"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        source_language = request.args.get('source_language')
        target_language = request.args.get('target_language')
        
        query = CustomDictionary.query.filter_by(is_active=True)
        
        if source_language:
            query = query.filter_by(source_language=source_language)
        
        if target_language:
            query = query.filter_by(target_language=target_language)
        
        entries = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [{
                'id': entry.id,
                'source_language': entry.source_language,
                'target_language': entry.target_language,
                'source_term': entry.source_term,
                'target_term': entry.target_term,
                'context': entry.context,
                'usage_count': entry.usage_count,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat()
            } for entry in entries.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': entries.total,
                'pages': entries.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting custom dictionary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/custom-dictionary', methods=['POST'])
@login_required
def add_custom_dictionary_entry():
    """Add a custom dictionary entry"""
    try:
        data = request.get_json()
        source_language = data.get('source_language')
        target_language = data.get('target_language')
        source_term = data.get('source_term')
        target_term = data.get('target_term')
        context = data.get('context')
        
        if not all([source_language, target_language, source_term, target_term]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        entry = translation_service.add_custom_dictionary_entry(
            source_language, target_language, source_term, target_term, context
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': entry.id,
                'source_language': entry.source_language,
                'target_language': entry.target_language,
                'source_term': entry.source_term,
                'target_term': entry.target_term,
                'context': entry.context,
                'usage_count': entry.usage_count,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding custom dictionary entry: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/sync-from-json', methods=['POST'])
@login_required
def sync_from_json():
    """Sync translations from JSON files to database"""
    try:
        data = request.get_json()
        language = data.get('language')
        
        if not language:
            return jsonify({'success': False, 'error': 'language is required'}), 400
        
        result = translation_service.sync_translations_from_json(language)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error syncing from JSON: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/export-to-json', methods=['POST'])
@login_required
def export_to_json():
    """Export translations from database to JSON format"""
    try:
        data = request.get_json()
        language = data.get('language')
        
        if not language:
            return jsonify({'success': False, 'error': 'language is required'}), 400
        
        result = translation_service.export_translations_to_json(language)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/missing-translations', methods=['GET'])
@login_required
def get_missing_translations():
    """Get list of missing translations"""
    try:
        source_language = request.args.get('source_language')
        target_language = request.args.get('target_language')
        
        missing = translation_service.get_missing_translations(source_language, target_language)
        
        return jsonify({
            'success': True,
            'data': missing,
            'count': len(missing)
        })
        
    except Exception as e:
        logger.error(f"Error getting missing translations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/stats', methods=['GET'])
@login_required
def get_translation_stats():
    """Get translation statistics"""
    try:
        stats = translation_service.get_translation_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting translation stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/memory', methods=['GET'])
@login_required
def get_translation_memory():
    """Get translation memory entries"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        source_language = request.args.get('source_language')
        target_language = request.args.get('target_language')
        
        query = TranslationMemory.query
        
        if source_language:
            query = query.filter_by(source_language=source_language)
        
        if target_language:
            query = query.filter_by(target_language=target_language)
        
        entries = query.order_by(TranslationMemory.usage_count.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [{
                'id': entry.id,
                'source_language': entry.source_language,
                'target_language': entry.target_language,
                'source_text': entry.source_text,
                'target_text': entry.target_text,
                'context': entry.context,
                'usage_count': entry.usage_count,
                'last_used': entry.last_used.isoformat(),
                'created_at': entry.created_at.isoformat()
            } for entry in entries.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': entries.total,
                'pages': entries.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting translation memory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@translations_bp.route('/logs', methods=['GET'])
@login_required
def get_translation_logs():
    """Get translation operation logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        operation_type = request.args.get('operation_type')
        
        query = TranslationLog.query
        
        if operation_type:
            query = query.filter_by(operation_type=operation_type)
        
        logs = query.order_by(TranslationLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [{
                'id': log.id,
                'operation_type': log.operation_type,
                'key_path': log.key_path,
                'source_language': log.source_language,
                'target_language': log.target_language,
                'user_id': log.user_id,
                'details': log.details,
                'created_at': log.created_at.isoformat()
            } for log in logs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': logs.total,
                'pages': logs.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting translation logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
