"""
Color Enhancement Service
========================

This service provides automated color contrast enhancement capabilities
for the PipLinePro application. It integrates with the color contrast
analyzer to automatically detect and improve problematic color combinations.

Features:
- Automated color analysis on application startup
- Real-time color improvement suggestions
- Professional business color palette management
- Integration with existing CSS files
- Background monitoring and reporting
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

from app.utils.color_contrast_analyzer import ColorContrastAnalyzer, ColorPair, ContrastResult

# Configure logging
logger = logging.getLogger(__name__)

class ColorEnhancementService:
    """
    Service for automated color contrast enhancement and management.
    
    This service provides comprehensive color analysis and improvement
    capabilities for professional business applications.
    """
    
    def __init__(self, app_root: str = None):
        """
        Initialize the color enhancement service.
        
        Args:
            app_root: Root directory of the application
        """
        self.app_root = app_root or os.getcwd()
        self.analyzer = ColorContrastAnalyzer()
        self.analysis_cache = {}
        self.improvement_history = []
        
        # Define CSS files to monitor
        self.css_files = [
            "static/css/bundle.min.css",
            "static/css/base/variables.css",
            "static/css/sidebar_fix.css"
        ]
        
        # Define template files to monitor
        self.template_files = [
            "templates/psp_ledger_content.html",
            "templates/transactions_content.html",
            "templates/dashboard.html",
            "templates/settings_main.html",
            "templates/view_transaction.html"
        ]
        
        logger.info("Color Enhancement Service initialized")
    
    def analyze_application_colors(self) -> Dict:
        """
        Perform comprehensive color analysis of the entire application.
        
        Returns:
            Dictionary containing analysis results and recommendations
        """
        logger.info("Starting comprehensive color analysis...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'css_issues': [],
            'template_issues': [],
            'total_issues': 0,
            'critical_issues': 0,
            'moderate_issues': 0,
            'minor_issues': 0,
            'improvements': [],
            'summary': {}
        }
        
        # Analyze CSS files
        for css_file in self.css_files:
            file_path = os.path.join(self.app_root, css_file)
            if os.path.exists(file_path):
                logger.info(f"Analyzing CSS file: {css_file}")
                css_results = self.analyzer.analyze_css_file(self._read_file(file_path))
                results['css_issues'].extend(css_results)
        
        # Analyze template files
        for template_file in self.template_files:
            file_path = os.path.join(self.app_root, template_file)
            if os.path.exists(file_path):
                logger.info(f"Analyzing template file: {template_file}")
                template_results = self._analyze_template_colors(self._read_file(file_path))
                results['template_issues'].extend(template_results)
        
        # Calculate statistics
        all_issues = results['css_issues'] + results['template_issues']
        results['total_issues'] = len(all_issues)
        
        for issue in all_issues:
            if issue.contrast_ratio < 3.0:
                results['critical_issues'] += 1
            elif issue.contrast_ratio < 4.5:
                results['moderate_issues'] += 1
            else:
                results['minor_issues'] += 1
        
        # Generate improvements
        if all_issues:
            results['improvements'] = self._generate_improvements(all_issues)
            results['summary'] = self.analyzer.generate_improvement_report(all_issues)
        
        # Cache results
        self.analysis_cache = results
        
        logger.info(f"Analysis complete. Found {results['total_issues']} issues")
        return results
    
    def _read_file(self, file_path: str) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def _analyze_template_colors(self, template_content: str) -> List[ContrastResult]:
        """Analyze colors in template files."""
        results = []
        
        # Extract color patterns from templates
        color_patterns = [
            (r'color:\s*(#[0-9a-fA-F]{3,6})', 'foreground'),
            (r'background-color:\s*(#[0-9a-fA-F]{3,6})', 'background'),
            (r'background:\s*(#[0-9a-fA-F]{3,6})', 'background'),
        ]
        
        colors = {}
        for pattern, color_type in color_patterns:
            import re
            matches = re.finditer(pattern, template_content, re.IGNORECASE)
            for match in matches:
                color = match.group(1)
                colors[color_type] = color
        
        # Create color pairs for analysis
        if 'foreground' in colors and 'background' in colors:
            pair = ColorPair(
                foreground=colors['foreground'],
                background=colors['background'],
                element_type="text",
                context="template_analysis"
            )
            result = self.analyzer.analyze_color_pair(pair)
            if not result.wcag_aa_passed:
                results.append(result)
        
        return results
    
    def _generate_improvements(self, issues: List[ContrastResult]) -> List[Dict]:
        """Generate improvement suggestions for detected issues."""
        improvements = []
        
        for issue in issues:
            if issue.suggested_foreground and issue.suggested_background:
                improvement = {
                    'original': {
                        'foreground': issue.foreground,
                        'background': issue.background,
                        'contrast_ratio': issue.contrast_ratio
                    },
                    'suggested': {
                        'foreground': issue.suggested_foreground,
                        'background': issue.suggested_background,
                        'contrast_ratio': self.analyzer.calculate_contrast_ratio(
                            issue.suggested_foreground,
                            issue.suggested_background
                        )
                    },
                    'improvement_score': issue.improvement_score,
                    'element_type': issue.element_type,
                    'context': issue.context
                }
                improvements.append(improvement)
        
        return improvements
    
    def generate_css_improvements(self) -> str:
        """
        Generate CSS improvements for detected contrast issues.
        
        Returns:
            CSS string with improvements
        """
        if not self.analysis_cache:
            self.analyze_application_colors()
        
        all_issues = self.analysis_cache['css_issues'] + self.analysis_cache['template_issues']
        
        if not all_issues:
            return "/* No contrast issues found */"
        
        return self.analyzer.create_css_fixes(all_issues)
    
    def save_improvements_to_file(self, output_file: str = "color_improvements.css") -> str:
        """
        Save generated improvements to a CSS file.
        
        Args:
            output_file: Name of the output CSS file
            
        Returns:
            Path to the saved file
        """
        css_content = self.generate_css_improvements()
        
        output_path = os.path.join(self.app_root, output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            logger.info(f"Improvements saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving improvements to {output_path}: {e}")
            return ""
    
    def get_analysis_report(self) -> Dict:
        """
        Get a formatted analysis report.
        
        Returns:
            Dictionary containing formatted analysis results
        """
        if not self.analysis_cache:
            self.analyze_application_colors()
        
        report = {
            'timestamp': self.analysis_cache['timestamp'],
            'summary': {
                'total_issues': self.analysis_cache['total_issues'],
                'critical_issues': self.analysis_cache['critical_issues'],
                'moderate_issues': self.analysis_cache['moderate_issues'],
                'minor_issues': self.analysis_cache['minor_issues'],
                'pass_rate': self._calculate_pass_rate(),
                'overall_score': self._calculate_overall_score()
            },
            'top_improvements': self._get_top_improvements(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _calculate_pass_rate(self) -> float:
        """Calculate the pass rate for color combinations."""
        total_tested = self.analysis_cache['total_issues']
        if total_tested == 0:
            return 100.0
        
        passed = total_tested - self.analysis_cache['critical_issues'] - self.analysis_cache['moderate_issues']
        return (passed / total_tested) * 100
    
    def _calculate_overall_score(self) -> float:
        """Calculate an overall color quality score."""
        if not self.analysis_cache['improvements']:
            return 100.0
        
        total_improvement = sum(imp['improvement_score'] for imp in self.analysis_cache['improvements'])
        avg_improvement = total_improvement / len(self.analysis_cache['improvements'])
        
        # Convert to a 0-100 score
        return max(0, min(100, 100 - (avg_improvement * 20)))
    
    def _get_top_improvements(self, limit: int = 5) -> List[Dict]:
        """Get the top improvement suggestions."""
        improvements = self.analysis_cache['improvements']
        sorted_improvements = sorted(improvements, key=lambda x: x['improvement_score'], reverse=True)
        return sorted_improvements[:limit]
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if self.analysis_cache['critical_issues'] > 0:
            recommendations.append(
                f"🔴 {self.analysis_cache['critical_issues']} critical contrast issues found. "
                "These should be addressed immediately for accessibility compliance."
            )
        
        if self.analysis_cache['moderate_issues'] > 0:
            recommendations.append(
                f"🟡 {self.analysis_cache['moderate_issues']} moderate contrast issues found. "
                "Consider improving these for better user experience."
            )
        
        if self.analysis_cache['total_issues'] == 0:
            recommendations.append("✅ No contrast issues found. Your color scheme is well-optimized!")
        else:
            recommendations.append(
                f"📈 Overall pass rate: {self._calculate_pass_rate():.1f}%. "
                "Consider applying the suggested improvements."
            )
        
        return recommendations
    
    def apply_improvements_automatically(self) -> bool:
        """
        Automatically apply the most critical improvements.
        
        Returns:
            True if improvements were applied successfully
        """
        try:
            # Generate improvements
            css_improvements = self.generate_css_improvements()
            
            if not css_improvements or css_improvements.strip() == "/* No contrast issues found */":
                logger.info("No improvements to apply")
                return True
            
            # Save to a new CSS file
            output_file = f"color_improvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.css"
            output_path = self.save_improvements_to_file(output_file)
            
            if output_path:
                logger.info(f"Improvements applied and saved to: {output_path}")
                return True
            else:
                logger.error("Failed to save improvements")
                return False
                
        except Exception as e:
            logger.error(f"Error applying improvements: {e}")
            return False
    
    def monitor_colors_continuously(self, interval_seconds: int = 300) -> None:
        """
        Start continuous color monitoring (for development/debugging).
        
        Args:
            interval_seconds: Monitoring interval in seconds
        """
        import threading
        import time
        
        def monitor_loop():
            while True:
                try:
                    logger.info("Running periodic color analysis...")
                    self.analyze_application_colors()
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Error in color monitoring: {e}")
                    time.sleep(interval_seconds)
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info(f"Color monitoring started (interval: {interval_seconds}s)")

# Global service instance
color_service = None

def get_color_service() -> ColorEnhancementService:
    """Get the global color enhancement service instance."""
    global color_service
    if color_service is None:
        color_service = ColorEnhancementService()
    return color_service

def initialize_color_service(app_root: str = None) -> ColorEnhancementService:
    """Initialize the color enhancement service."""
    global color_service
    color_service = ColorEnhancementService(app_root)
    return color_service 