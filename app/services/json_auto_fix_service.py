"""
DEPRECATED: This service is deprecated.
Do not use for new code.
"""
import json
import re
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

class JSONAutoFixService:
    """
    DEPRECATED SERVICE
    """
    def safe_json_loads(self, text: str, **kwargs) -> Any:
        """Deprecated safe_json_loads"""
        logger.warning("Using deprecated safe_json_loads. Fix the data source instead.")
        try:
            return json.loads(text, **kwargs)
        except Exception:
            # For legacy compatibility, we might still need this, but we should log it heavily
            pass
        return {}

    def safe_json_dumps(self, obj: Any, **kwargs) -> str:
        """Deprecated safe_json_dumps"""
        return json.dumps(obj, default=str, **kwargs)

    def auto_fix_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deprecated auto_fix_template_data"""
        return data

json_auto_fix_service = JSONAutoFixService()
safe_json_loads = json_auto_fix_service.safe_json_loads
safe_json_dumps = json_auto_fix_service.safe_json_dumps