"""
Endpoint Auditor
Utility to check if all endpoints use proper decorators
"""
import ast
import os
from pathlib import Path
from typing import List, Dict, Tuple
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


class EndpointAuditor:
    """Audit endpoints for proper decorator usage"""
    
    def __init__(self):
        self.missing_error_handler: List[Tuple[str, str]] = []
        self.missing_csrf: List[Tuple[str, str]] = []
        self.missing_validation: List[Tuple[str, str]] = []
    
    def audit_file(self, file_path: Path) -> Dict[str, List[Tuple[str, str]]]:
        """
        Audit a Python file for endpoint decorators
        
        Args:
            file_path: Path to Python file
        
        Returns:
            Dictionary with audit results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function is a route handler
                    decorator_names = []
                    for decorator in node.decorator_list:
                        # Handle @decorator, @decorator(), @module.decorator, etc.
                        if isinstance(decorator, ast.Name):
                            decorator_names.append(decorator.id)
                        elif isinstance(decorator, ast.Attribute):
                            decorator_names.append(decorator.attr)
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                decorator_names.append(decorator.func.id)
                            elif isinstance(decorator.func, ast.Attribute):
                                decorator_names.append(decorator.func.attr)
                    
                    # Only check functions with route decorators (more specific)
                    has_route = any(
                        isinstance(d, ast.Call) and 
                        isinstance(d.func, ast.Attribute) and
                        d.func.attr == 'route'
                        for d in node.decorator_list
                    )
                    
                    if has_route:
                        # Check for required decorators
                        has_error_handler = any('handle_api_errors' in dec for dec in decorator_names)
                        has_csrf = any('csrf' in dec.lower() for dec in decorator_names)
                        has_validation = any('validate' in dec.lower() for dec in decorator_names)
                        
                        # Check HTTP method
                        method = self._get_http_method(decorator_names)
                        needs_csrf = method in ('POST', 'PUT', 'DELETE', 'PATCH')
                        needs_validation = method in ('POST', 'PUT', 'PATCH')
                        
                        file_str = str(file_path)
                        func_name = f"{file_path.stem}.{node.name}"
                        
                        if not has_error_handler:
                            self.missing_error_handler.append((file_str, func_name))
                        
                        if needs_csrf and not has_csrf:
                            self.missing_csrf.append((file_str, func_name))
                        
                        if needs_validation and not has_validation:
                            self.missing_validation.append((file_str, func_name))
        
        except Exception as e:
            logger.warning(f"Error auditing {file_path}: {e}")
        
        return {
            'missing_error_handler': self.missing_error_handler,
            'missing_csrf': self.missing_csrf,
            'missing_validation': self.missing_validation
        }
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return str(decorator)
    
    def _get_http_method(self, decorators: List[str]) -> Optional[str]:
        """Extract HTTP method from decorators"""
        for dec in decorators:
            if 'methods' in dec.lower():
                # Try to extract method from decorator
                if 'POST' in dec.upper():
                    return 'POST'
                elif 'PUT' in dec.upper():
                    return 'PUT'
                elif 'DELETE' in dec.upper():
                    return 'DELETE'
                elif 'PATCH' in dec.upper():
                    return 'PATCH'
                elif 'GET' in dec.upper():
                    return 'GET'
        return None
    
    def audit_directory(self, directory: Path) -> Dict[str, List[Tuple[str, str]]]:
        """
        Audit all Python files in a directory
        
        Args:
            directory: Directory to audit
        
        Returns:
            Dictionary with audit results
        """
        results = {
            'missing_error_handler': [],
            'missing_csrf': [],
            'missing_validation': []
        }
        
        for file_path in directory.rglob('*.py'):
            if '__pycache__' in str(file_path) or 'test' in str(file_path).lower():
                continue
            
            file_results = self.audit_file(file_path)
            for key in results:
                results[key].extend(file_results[key])
        
        return results
    
    def generate_report(self, results: Dict[str, List[Tuple[str, str]]]) -> str:
        """
        Generate audit report
        
        Args:
            results: Audit results
        
        Returns:
            Formatted report string
        """
        report = ["=" * 70]
        report.append("ENDPOINT AUDIT REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Missing error handlers
        report.append(f"Missing @handle_api_errors: {len(results['missing_error_handler'])}")
        for file_path, func_name in results['missing_error_handler'][:10]:
            report.append(f"  - {func_name} in {file_path}")
        if len(results['missing_error_handler']) > 10:
            report.append(f"  ... and {len(results['missing_error_handler']) - 10} more")
        report.append("")
        
        # Missing CSRF
        report.append(f"Missing CSRF protection: {len(results['missing_csrf'])}")
        for file_path, func_name in results['missing_csrf'][:10]:
            report.append(f"  - {func_name} in {file_path}")
        if len(results['missing_csrf']) > 10:
            report.append(f"  ... and {len(results['missing_csrf']) - 10} more")
        report.append("")
        
        # Missing validation
        report.append(f"Missing input validation: {len(results['missing_validation'])}")
        for file_path, func_name in results['missing_validation'][:10]:
            report.append(f"  - {func_name} in {file_path}")
        if len(results['missing_validation']) > 10:
            report.append(f"  ... and {len(results['missing_validation']) - 10} more")
        report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def audit_endpoints():
    """Audit all API endpoints"""
    auditor = EndpointAuditor()
    api_dir = Path('app/api')
    
    if api_dir.exists():
        results = auditor.audit_directory(api_dir)
        report = auditor.generate_report(results)
        logger.info(f"\n{report}")
        return results
    
    return {}

