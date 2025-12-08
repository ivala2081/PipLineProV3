import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app
from app import db
from app.models.translation import (
    TranslationKey, Translation, CustomDictionary, 
    TranslationMemory, TranslationLog, TranslationSettings
)
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


class TranslationService:
    """Comprehensive translation service with automation and custom dictionary support"""
    
    def __init__(self):
        self.supported_languages = ['en', 'tr', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar']
        self.default_language = 'en'
        # Don't load settings in __init__ to avoid context issues
        self._settings_loaded = False
    
    def _load_settings(self):
        """Load translation settings from database"""
        if self._settings_loaded:
            return
        
        try:
            # Only try to load if we have an app context
            try:
                from flask import current_app
                if current_app:
                    settings = TranslationSettings.query.all()
                    for setting in settings:
                        if setting.setting_key == 'supported_languages':
                            self.supported_languages = setting.setting_value
                        elif setting.setting_key == 'default_language':
                            self.default_language = setting.setting_value
                    self._settings_loaded = True
            except RuntimeError:
                # No app context available, use defaults
                logger.debug("No app context available for loading translation settings, using defaults")
        except Exception as e:
            logger.warning(f"Could not load translation settings: {e}")
    
    def _ensure_settings_loaded(self):
        """Ensure settings are loaded before operations"""
        if not self._settings_loaded:
            self._load_settings()
    
    def get_translation(self, key_path: str, language: str, params: Optional[Dict] = None) -> str:
        """Get translation for a specific key and language"""
        try:
            self._ensure_settings_loaded()
            # First check database
            translation = self._get_from_database(key_path, language)
            if translation:
                text = translation.translation_text
            else:
                # Fallback to JSON files
                text = self._get_from_json_files(key_path, language)
            
            # Apply custom dictionary substitutions
            text = self._apply_custom_dictionary(text, language)
            
            # Replace parameters
            if params:
                text = self._replace_parameters(text, params)
            
            return text or key_path
            
        except Exception as e:
            logger.error(f"Error getting translation for {key_path} in {language}: {e}")
            return key_path
    
    def _get_from_database(self, key_path: str, language: str) -> Optional[Translation]:
        """Get translation from database"""
        try:
            key = TranslationKey.query.filter_by(key_path=key_path, is_active=True).first()
            if key:
                return Translation.query.filter_by(
                    key_id=key.id, 
                    language_code=language
                ).first()
        except Exception as e:
            logger.error(f"Database error getting translation: {e}")
        return None
    
    def _get_from_json_files(self, key_path: str, language: str) -> str:
        """Get translation from JSON files (fallback)"""
        try:
            json_path = f"frontend/src/locales/{language}.json"
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Navigate through nested keys
                keys = key_path.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return ""
                
                return str(value) if value else ""
        except Exception as e:
            logger.error(f"Error reading JSON file for {language}: {e}")
        return ""
    
    def _apply_custom_dictionary(self, text: str, language: str) -> str:
        """Apply custom dictionary substitutions"""
        try:
            self._ensure_settings_loaded()
            if language == self.default_language:
                return text
            
            # Get custom dictionary entries for this language pair
            custom_entries = CustomDictionary.query.filter_by(
                source_language=self.default_language,
                target_language=language,
                is_active=True
            ).all()
            
            for entry in custom_entries:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(entry.source_term) + r'\b'
                text = re.sub(pattern, entry.target_term, text, flags=re.IGNORECASE)
                
                # Update usage count
                entry.usage_count += 1
                entry.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            return text
            
        except Exception as e:
            logger.error(f"Error applying custom dictionary: {e}")
            return text
    
    def _replace_parameters(self, text: str, params: Dict) -> str:
        """Replace parameters in translation text"""
        try:
            import re
            return re.sub(r'\{(\w+)\}', lambda match: str(params.get(match.group(1), match.group(0))), text)
        except Exception as e:
            logger.error(f"Error replacing parameters: {e}")
            return text
    
    def add_translation_key(self, key_path: str, description: str = None, context: str = None) -> TranslationKey:
        """Add a new translation key"""
        try:
            # Check if key already exists
            existing_key = TranslationKey.query.filter_by(key_path=key_path).first()
            if existing_key:
                return existing_key
            
            key = TranslationKey(
                key_path=key_path,
                description=description,
                context=context
            )
            db.session.add(key)
            db.session.commit()
            
            self._log_operation('create', key_path=key_path, details={'description': description, 'context': context})
            return key
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding translation key: {e}")
            raise
    
    def add_translation(self, key_path: str, language: str, text: str, 
                       is_approved: bool = False, is_auto_translated: bool = False,
                       confidence_score: float = 0.0) -> Translation:
        """Add or update a translation"""
        try:
            # Get or create translation key
            key = TranslationKey.query.filter_by(key_path=key_path).first()
            if not key:
                key = self.add_translation_key(key_path)
            
            # Check if translation already exists
            translation = Translation.query.filter_by(
                key_id=key.id, 
                language_code=language
            ).first()
            
            if translation:
                # Update existing translation
                translation.translation_text = text
                translation.is_approved = is_approved
                translation.is_auto_translated = is_auto_translated
                translation.confidence_score = confidence_score
                translation.updated_at = datetime.now(timezone.utc)
            else:
                # Create new translation
                translation = Translation(
                    key_id=key.id,
                    language_code=language,
                    translation_text=text,
                    is_approved=is_approved,
                    is_auto_translated=is_auto_translated,
                    confidence_score=confidence_score
                )
                db.session.add(translation)
            
            db.session.commit()
            
            # Add to translation memory
            self._add_to_translation_memory(key_path, language, text)
            
            self._log_operation('update', key_path=key_path, source_language=self.default_language, 
                              target_language=language, details={'text': text, 'auto_translated': is_auto_translated})
            
            return translation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding translation: {e}")
            raise
    
    def auto_translate(self, key_path: str, target_language: str, 
                      source_language: str = None) -> Optional[str]:
        """Automatically translate a key using various methods"""
        try:
            if not source_language:
                source_language = self.default_language
            
            if target_language == source_language:
                return None
            
            # First check translation memory
            memory_translation = self._get_from_translation_memory(key_path, source_language, target_language)
            if memory_translation:
                return memory_translation
            
            # Get source text
            source_text = self.get_translation(key_path, source_language)
            if not source_text or source_text == key_path:
                return None
            
            # Try to translate using simple methods first
            translated_text = self._simple_translate(source_text, source_language, target_language)
            
            if translated_text:
                # Add to database
                self.add_translation(key_path, target_language, translated_text, 
                                   is_auto_translated=True, confidence_score=0.7)
                return translated_text
            
            return None
            
        except Exception as e:
            logger.error(f"Error in auto translation: {e}")
            return None
    
    def _get_from_translation_memory(self, key_path: str, source_language: str, target_language: str) -> Optional[str]:
        """Get translation from memory"""
        try:
            # Get source text
            source_text = self.get_translation(key_path, source_language)
            if not source_text:
                return None
            
            memory = TranslationMemory.query.filter_by(
                source_language=source_language,
                target_language=target_language,
                source_text=source_text
            ).first()
            
            if memory:
                # Update usage count and last used
                memory.usage_count += 1
                memory.last_used = datetime.now(timezone.utc)
                db.session.commit()
                return memory.target_text
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from translation memory: {e}")
            return None
    
    def _add_to_translation_memory(self, key_path: str, language: str, text: str):
        """Add translation to memory"""
        try:
            source_text = self.get_translation(key_path, self.default_language)
            if not source_text or source_text == key_path:
                return
            
            # Check if already exists
            existing = TranslationMemory.query.filter_by(
                source_language=self.default_language,
                target_language=language,
                source_text=source_text
            ).first()
            
            if existing:
                existing.target_text = text
                existing.last_used = datetime.now(timezone.utc)
            else:
                memory = TranslationMemory(
                    source_language=self.default_language,
                    target_language=language,
                    source_text=source_text,
                    target_text=text
                )
                db.session.add(memory)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error adding to translation memory: {e}")
    
    def _simple_translate(self, text: str, source_language: str, target_language: str) -> Optional[str]:
        """Simple translation using custom dictionary and patterns"""
        try:
            # Apply custom dictionary first
            translated = self._apply_custom_dictionary(text, target_language)
            
            # If text changed, it means custom dictionary was applied
            if translated != text:
                return translated
            
            # For now, return None to indicate no simple translation available
            # In a real implementation, you might integrate with translation APIs here
            return None
            
        except Exception as e:
            logger.error(f"Error in simple translation: {e}")
            return None
    
    def add_custom_dictionary_entry(self, source_language: str, target_language: str, 
                                  source_term: str, target_term: str, context: str = None) -> CustomDictionary:
        """Add a custom dictionary entry"""
        try:
            # Check if entry already exists
            existing = CustomDictionary.query.filter_by(
                source_language=source_language,
                target_language=target_language,
                source_term=source_term
            ).first()
            
            if existing:
                existing.target_term = target_term
                existing.context = context
                existing.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                return existing
            
            entry = CustomDictionary(
                source_language=source_language,
                target_language=target_language,
                source_term=source_term,
                target_term=target_term,
                context=context
            )
            db.session.add(entry)
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding custom dictionary entry: {e}")
            raise
    
    def sync_translations_from_json(self, language: str) -> Dict[str, Any]:
        """Sync translations from JSON files to database"""
        try:
            json_path = f"frontend/src/locales/{language}.json"
            if not os.path.exists(json_path):
                return {"success": False, "error": f"JSON file not found: {json_path}"}
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            added_count = 0
            updated_count = 0
            
            def process_nested_dict(d: Dict, prefix: str = ""):
                nonlocal added_count, updated_count
                
                for key, value in d.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        process_nested_dict(value, current_path)
                    elif isinstance(value, str):
                        # Add translation key and translation
                        try:
                            translation_key = self.add_translation_key(current_path)
                            translation = self.add_translation(current_path, language, value)
                            
                            if translation.created_at == translation.updated_at:
                                added_count += 1
                            else:
                                updated_count += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing {current_path}: {e}")
            
            process_nested_dict(data)
            
            return {
                "success": True,
                "added": added_count,
                "updated": updated_count,
                "total": added_count + updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing translations from JSON: {e}")
            return {"success": False, "error": str(e)}
    
    def export_translations_to_json(self, language: str) -> Dict[str, Any]:
        """Export translations from database to JSON format"""
        try:
            translations = db.session.query(Translation, TranslationKey).join(
                TranslationKey, Translation.key_id == TranslationKey.id
            ).filter(
                Translation.language_code == language,
                TranslationKey.is_active == True
            ).all()
            
            # Build nested dictionary structure
            data = {}
            for translation, key in translations:
                keys = key.key_path.split('.')
                current = data
                
                for i, k in enumerate(keys[:-1]):
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                current[keys[-1]] = translation.translation_text
            
            return {
                "success": True,
                "data": data,
                "count": len(translations)
            }
            
        except Exception as e:
            logger.error(f"Error exporting translations to JSON: {e}")
            return {"success": False, "error": str(e)}
    
    def get_missing_translations(self, source_language: str = None, target_language: str = None) -> List[Dict]:
        """Get list of missing translations"""
        try:
            if not source_language:
                source_language = self.default_language
            
            # Get all translation keys
            keys = TranslationKey.query.filter_by(is_active=True).all()
            missing = []
            
            for key in keys:
                # Check if translation exists for target language
                if target_language:
                    translation = Translation.query.filter_by(
                        key_id=key.id, 
                        language_code=target_language
                    ).first()
                    
                    if not translation:
                        # Get source translation for reference
                        source_translation = Translation.query.filter_by(
                            key_id=key.id, 
                            language_code=source_language
                        ).first()
                        
                        missing.append({
                            "key_path": key.key_path,
                            "source_text": source_translation.translation_text if source_translation else "",
                            "context": key.context,
                            "description": key.description
                        })
                else:
                    # Check all languages
                    for lang in self.supported_languages:
                        if lang == source_language:
                            continue
                        
                        translation = Translation.query.filter_by(
                            key_id=key.id, 
                            language_code=lang
                        ).first()
                        
                        if not translation:
                            source_translation = Translation.query.filter_by(
                                key_id=key.id, 
                                language_code=source_language
                            ).first()
                            
                            missing.append({
                                "key_path": key.key_path,
                                "target_language": lang,
                                "source_text": source_translation.translation_text if source_translation else "",
                                "context": key.context,
                                "description": key.description
                            })
            
            return missing
            
        except Exception as e:
            logger.error(f"Error getting missing translations: {e}")
            return []
    
    def bulk_translate(self, translations: List[Dict]) -> Dict[str, Any]:
        """Bulk translate multiple keys"""
        try:
            results = {
                "success": 0,
                "failed": 0,
                "errors": []
            }
            
            for item in translations:
                try:
                    key_path = item.get("key_path")
                    target_language = item.get("target_language")
                    source_language = item.get("source_language", self.default_language)
                    
                    if not key_path or not target_language:
                        results["failed"] += 1
                        results["errors"].append(f"Missing key_path or target_language: {item}")
                        continue
                    
                    # Try auto translation
                    translated_text = self.auto_translate(key_path, target_language, source_language)
                    
                    if translated_text:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Could not translate: {key_path}")
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error translating {item}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk translation: {e}")
            return {"success": 0, "failed": len(translations), "errors": [str(e)]}
    
    def _log_operation(self, operation_type: str, **kwargs):
        """Log translation operation"""
        try:
            log = TranslationLog(
                operation_type=operation_type,
                **kwargs
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging translation operation: {e}")
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """Get translation statistics"""
        try:
            total_keys = TranslationKey.query.filter_by(is_active=True).count()
            total_translations = Translation.query.count()
            auto_translated = Translation.query.filter_by(is_auto_translated=True).count()
            approved = Translation.query.filter_by(is_approved=True).count()
            
            # Count by language
            language_stats = {}
            for lang in self.supported_languages:
                count = Translation.query.filter_by(language_code=lang).count()
                language_stats[lang] = count
            
            # Custom dictionary stats
            custom_dict_count = CustomDictionary.query.filter_by(is_active=True).count()
            
            # Translation memory stats
            memory_count = TranslationMemory.query.count()
            
            return {
                "total_keys": total_keys,
                "total_translations": total_translations,
                "auto_translated": auto_translated,
                "approved": approved,
                "language_stats": language_stats,
                "custom_dictionary_entries": custom_dict_count,
                "translation_memory_entries": memory_count,
                "completion_rate": (total_translations / (total_keys * len(self.supported_languages))) * 100 if total_keys > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting translation stats: {e}")
            return {}
