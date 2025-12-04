"""
Color Contrast Analyzer and Enhancement System
============================================

This module provides automated color contrast analysis and improvement
for professional business applications. It detects problematic color
combinations and suggests better alternatives that meet WCAG standards.

Features:
- WCAG 2.1 AA/AAA compliance checking
- Automatic color suggestion based on business standards
- Professional color palette management
- Contrast ratio calculations
- Color accessibility validation
"""

import re
import colorsys
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
import logging

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ColorPair:
    """Represents a foreground/background color pair for analysis."""
    foreground: str
    background: str
    element_type: str = "text"
    context: str = "general"

@dataclass
class ContrastResult:
    """Results of contrast analysis for a color pair."""
    foreground: str
    background: str
    contrast_ratio: float
    wcag_aa_passed: bool
    wcag_aaa_passed: bool
    element_type: str
    context: str
    suggested_foreground: Optional[str] = None
    suggested_background: Optional[str] = None
    improvement_score: float = 0.0

class ColorContrastAnalyzer:
    """
    Automated color contrast analyzer and improvement system.
    
    This class provides comprehensive color analysis and improvement
    capabilities for professional business applications.
    """
    
    # WCAG 2.1 Contrast Requirements
    WCAG_AA_NORMAL = 4.5  # Normal text
    WCAG_AA_LARGE = 3.0   # Large text (18pt+ or 14pt+ bold)
    WCAG_AAA_NORMAL = 7.0 # AAA normal text
    WCAG_AAA_LARGE = 4.5  # AAA large text
    
    # Professional Business Color Palette
    PROFESSIONAL_COLORS = {
        'primary': {
            'blue': '#2563eb',
            'dark_blue': '#1d4ed8',
            'light_blue': '#3b82f6',
            'navy': '#1e3a8a'
        },
        'text': {
            'primary': '#1e293b',
            'secondary': '#475569',
            'muted': '#64748b',
            'light': '#94a3b8',
            'white': '#ffffff'
        },
        'background': {
            'white': '#ffffff',
            'light_gray': '#f8fafc',
            'gray': '#f1f5f9',
            'dark': '#1e293b'
        },
        'status': {
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#06b6d4'
        }
    }
    
    def __init__(self):
        """Initialize the color contrast analyzer."""
        self.problematic_colors = []
        self.improvements = []
        
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB values."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB values to hex color."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def get_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance of a color."""
        def normalize(value):
            value = value / 255.0
            return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
        
        r, g, b = rgb
        return 0.2126 * normalize(r) + 0.7152 * normalize(g) + 0.0722 * normalize(b)
    
    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors."""
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        
        lum1 = self.get_luminance(rgb1)
        lum2 = self.get_luminance(rgb2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def check_wcag_compliance(self, contrast_ratio: float, element_type: str = "text") -> Tuple[bool, bool]:
        """Check if contrast ratio meets WCAG AA and AAA standards."""
        if element_type in ["large_text", "heading"]:
            aa_passed = contrast_ratio >= self.WCAG_AA_LARGE
            aaa_passed = contrast_ratio >= self.WCAG_AAA_LARGE
        else:
            aa_passed = contrast_ratio >= self.WCAG_AA_NORMAL
            aaa_passed = contrast_ratio >= self.WCAG_AAA_NORMAL
            
        return aa_passed, aaa_passed
    
    def analyze_color_pair(self, color_pair: ColorPair) -> ContrastResult:
        """Analyze a single color pair for contrast issues."""
        try:
            contrast_ratio = self.calculate_contrast_ratio(color_pair.foreground, color_pair.background)
            aa_passed, aaa_passed = self.check_wcag_compliance(contrast_ratio, color_pair.element_type)
            
            # Determine if improvement is needed
            needs_improvement = not aa_passed
            
            # Generate suggestions if needed
            suggested_fg = None
            suggested_bg = None
            improvement_score = 0.0
            
            if needs_improvement:
                suggested_fg, suggested_bg = self.suggest_better_colors(
                    color_pair.foreground, 
                    color_pair.background,
                    color_pair.element_type
                )
                improvement_score = self.calculate_improvement_score(
                    contrast_ratio, 
                    self.calculate_contrast_ratio(suggested_fg, suggested_bg)
                )
            
            return ContrastResult(
                foreground=color_pair.foreground,
                background=color_pair.background,
                contrast_ratio=contrast_ratio,
                wcag_aa_passed=aa_passed,
                wcag_aaa_passed=aaa_passed,
                element_type=color_pair.element_type,
                context=color_pair.context,
                suggested_foreground=suggested_fg,
                suggested_background=suggested_bg,
                improvement_score=improvement_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing color pair {color_pair}: {e}")
            return ContrastResult(
                foreground=color_pair.foreground,
                background=color_pair.background,
                contrast_ratio=0.0,
                wcag_aa_passed=False,
                wcag_aaa_passed=False,
                element_type=color_pair.element_type,
                context=color_pair.context
            )
    
    def suggest_better_colors(self, fg: str, bg: str, element_type: str) -> Tuple[str, str]:
        """Suggest better color combinations for professional business use."""
        # Analyze current colors
        fg_rgb = self.hex_to_rgb(fg)
        bg_rgb = self.hex_to_rgb(bg)
        
        # Determine if we need to adjust foreground or background
        fg_luminance = self.get_luminance(fg_rgb)
        bg_luminance = self.get_luminance(bg_rgb)
        
        # Professional color suggestions based on context
        if element_type in ["text", "body"]:
            if bg_luminance > 0.5:  # Light background
                suggested_fg = self.PROFESSIONAL_COLORS['text']['primary']
                suggested_bg = bg  # Keep background
            else:  # Dark background
                suggested_fg = self.PROFESSIONAL_COLORS['text']['white']
                suggested_bg = bg  # Keep background
                
        elif element_type in ["heading", "title"]:
            suggested_fg = self.PROFESSIONAL_COLORS['text']['primary']
            suggested_bg = bg
            
        elif element_type in ["muted", "secondary"]:
            suggested_fg = self.PROFESSIONAL_COLORS['text']['secondary']
            suggested_bg = bg
            
        elif element_type in ["success", "warning", "danger", "info"]:
            status_type = element_type
            suggested_fg = self.PROFESSIONAL_COLORS['status'][status_type]
            suggested_bg = bg
            
        else:
            # Default to high contrast
            if bg_luminance > 0.5:
                suggested_fg = self.PROFESSIONAL_COLORS['text']['primary']
            else:
                suggested_fg = self.PROFESSIONAL_COLORS['text']['white']
            suggested_bg = bg
            
        return suggested_fg, suggested_bg
    
    def calculate_improvement_score(self, current_ratio: float, new_ratio: float) -> float:
        """Calculate how much the contrast ratio improves."""
        if current_ratio <= 0:
            return 0.0
        
        improvement = (new_ratio - current_ratio) / current_ratio
        return max(0.0, min(1.0, improvement))
    
    def extract_colors_from_css(self, css_content: str) -> List[ColorPair]:
        """Extract color pairs from CSS content for analysis."""
        color_pairs = []
        
        # Common problematic color patterns
        problematic_patterns = [
            (r'color:\s*(#[0-9a-fA-F]{3,6})', 'foreground'),
            (r'background-color:\s*(#[0-9a-fA-F]{3,6})', 'background'),
            (r'background:\s*(#[0-9a-fA-F]{3,6})', 'background'),
        ]
        
        # Extract color declarations
        colors = {}
        for pattern, color_type in problematic_patterns:
            matches = re.finditer(pattern, css_content, re.IGNORECASE)
            for match in matches:
                color = match.group(1)
                colors[color_type] = color
        
        # Create color pairs for analysis
        if 'foreground' in colors and 'background' in colors:
            color_pairs.append(ColorPair(
                foreground=colors['foreground'],
                background=colors['background'],
                element_type="text",
                context="css_extraction"
            ))
        
        return color_pairs
    
    def analyze_css_file(self, css_content: str) -> List[ContrastResult]:
        """Analyze an entire CSS file for contrast issues."""
        color_pairs = self.extract_colors_from_css(css_content)
        results = []
        
        for pair in color_pairs:
            result = self.analyze_color_pair(pair)
            if not result.wcag_aa_passed:
                results.append(result)
                
        return results
    
    def generate_improvement_report(self, results: List[ContrastResult]) -> Dict:
        """Generate a comprehensive improvement report."""
        report = {
            'total_issues': len(results),
            'critical_issues': len([r for r in results if r.contrast_ratio < 3.0]),
            'moderate_issues': len([r for r in results if 3.0 <= r.contrast_ratio < 4.5]),
            'minor_issues': len([r for r in results if r.contrast_ratio >= 4.5]),
            'improvements': [],
            'summary': {
                'avg_improvement_score': 0.0,
                'total_improvements': 0
            }
        }
        
        total_improvement = 0.0
        improvement_count = 0
        
        for result in results:
            if result.suggested_foreground and result.suggested_background:
                improvement = {
                    'original': {
                        'foreground': result.foreground,
                        'background': result.background,
                        'contrast_ratio': result.contrast_ratio
                    },
                    'suggested': {
                        'foreground': result.suggested_foreground,
                        'background': result.suggested_background,
                        'contrast_ratio': self.calculate_contrast_ratio(
                            result.suggested_foreground, 
                            result.suggested_background
                        )
                    },
                    'improvement_score': result.improvement_score,
                    'element_type': result.element_type,
                    'context': result.context
                }
                report['improvements'].append(improvement)
                
                total_improvement += result.improvement_score
                improvement_count += 1
        
        if improvement_count > 0:
            report['summary']['avg_improvement_score'] = total_improvement / improvement_count
            report['summary']['total_improvements'] = improvement_count
            
        return report
    
    def create_css_fixes(self, results: List[ContrastResult]) -> str:
        """Generate CSS fixes for contrast issues."""
        css_fixes = []
        css_fixes.append("/* ===== AUTOMATED CONTRAST IMPROVEMENTS ===== */")
        css_fixes.append("/* Generated by Color Contrast Analyzer */")
        css_fixes.append("")
        
        for result in results:
            if result.suggested_foreground and result.suggested_background:
                # Create CSS rule for the improvement
                css_fixes.append(f"/* Fix for {result.context} - {result.element_type} */")
                css_fixes.append(f"/* Original: {result.foreground} on {result.background} (ratio: {result.contrast_ratio:.2f}) */")
                css_fixes.append(f"/* Improved: {result.suggested_foreground} on {result.suggested_background} */")
                css_fixes.append("")
                
                # Add the actual CSS rule (this would need to be customized based on selectors)
                css_fixes.append(f"/* Add appropriate selector for this improvement */")
                css_fixes.append(f"/* color: {result.suggested_foreground} !important; */")
                css_fixes.append("")
        
        return "\n".join(css_fixes)

# Utility functions for easy use
def analyze_file_colors(file_path: str) -> List[ContrastResult]:
    """Analyze colors in a specific file."""
    analyzer = ColorContrastAnalyzer()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return analyzer.analyze_css_file(content)
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return []

def generate_improvement_css(results: List[ContrastResult]) -> str:
    """Generate CSS improvements for contrast issues."""
    analyzer = ColorContrastAnalyzer()
    return analyzer.create_css_fixes(results)

def test_color_contrast():
    """Test function to validate the color contrast analyzer."""
    analyzer = ColorContrastAnalyzer()
    
    # Test problematic color combinations
    test_pairs = [
        ColorPair("#6c757d", "#ffffff", "text", "test"),  # Common problematic gray
        ColorPair("#495057", "#f8f9fa", "text", "test"),  # Another problematic gray
        ColorPair("#212529", "#ffffff", "text", "test"),  # Should be fine
        ColorPair("#64748b", "#f1f5f9", "text", "test"), # Another gray
    ]
    
    # Color Contrast Analysis Test
    for pair in test_pairs:
        result = analyzer.analyze_color_pair(pair)
        # Analyze color pair results
        pass
        
        if result.suggested_foreground:
            # Color improvement suggestions available
            pass

# if __name__ == "__main__":
#     test_color_contrast() 