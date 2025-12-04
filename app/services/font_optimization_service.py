"""
Font Optimization Service for PipLine Pro
Manages font loading, performance optimization, and provides font recommendations
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = logging.getLogger(__name__)

@dataclass
class FontMetrics:
    """Font usage metrics and performance data"""
    font_family: str
    font_weight: int
    usage_count: int
    load_time: float
    file_size: int
    last_used: datetime
    performance_score: float
    accessibility_score: float

@dataclass
class FontRecommendation:
    """Font recommendation for specific use cases"""
    use_case: str
    primary_font: str
    fallback_fonts: List[str]
    font_weights: List[int]
    reasoning: str
    performance_impact: str

class FontOptimizationService:
    """Service for optimizing font loading and performance"""
    
    def __init__(self):
        self.font_cache_file = "instance/font_metrics.json"
        self.font_metrics: Dict[str, FontMetrics] = {}
        self.recommendations: Dict[str, FontRecommendation] = {}
        self.load_font_metrics()
        self._initialize_recommendations()
    
    def _initialize_recommendations(self):
        """Initialize default font recommendations"""
        self.recommendations = {
            "headings": FontRecommendation(
                use_case="Headings and Titles",
                primary_font="Inter",
                fallback_fonts=["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto"],
                font_weights=[600, 700],
                reasoning="Inter provides excellent readability and modern appearance for headings",
                performance_impact="Low - Optimized with font-display: swap"
            ),
            "body": FontRecommendation(
                use_case="Body Text and Content",
                primary_font="Inter",
                fallback_fonts=["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto"],
                font_weights=[400, 500],
                reasoning="Inter offers superior legibility and consistent rendering across devices",
                performance_impact="Low - Preloaded critical weights"
            ),
            "ui": FontRecommendation(
                use_case="User Interface Elements",
                primary_font="Inter",
                fallback_fonts=["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto"],
                font_weights=[400, 500, 600],
                reasoning="Inter provides clear, readable text for buttons, labels, and navigation",
                performance_impact="Low - Optimized loading strategy"
            ),
            "monospace": FontRecommendation(
                use_case="Code and Technical Data",
                primary_font="SF Mono",
                fallback_fonts=["Monaco", "Cascadia Code", "Roboto Mono", "Consolas", "Courier New"],
                font_weights=[400],
                reasoning="Monospace fonts ensure consistent character width for code and data",
                performance_impact="Minimal - System fonts used as fallbacks"
            ),
            "display": FontRecommendation(
                use_case="Display and Brand Elements",
                primary_font="Inter",
                fallback_fonts=["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto"],
                font_weights=[700, 800],
                reasoning="Inter provides strong visual impact for brand elements and large text",
                performance_impact="Low - Strategic weight loading"
            )
        }
    
    def load_font_metrics(self):
        """Load font metrics from cache file"""
        try:
            if os.path.exists(self.font_cache_file):
                with open(self.font_cache_file, 'r') as f:
                    data = json.load(f)
                    for key, metrics_data in data.items():
                        metrics_data['last_used'] = datetime.fromisoformat(metrics_data['last_used'])
                        self.font_metrics[key] = FontMetrics(**metrics_data)
                logger.info(f"Loaded {len(self.font_metrics)} font metrics from cache")
        except Exception as e:
            logger.warning(f"Could not load font metrics: {e}")
    
    def save_font_metrics(self):
        """Save font metrics to cache file"""
        try:
            os.makedirs(os.path.dirname(self.font_cache_file), exist_ok=True)
            data = {}
            for key, metrics in self.font_metrics.items():
                metrics_dict = asdict(metrics)
                metrics_dict['last_used'] = metrics.last_used.isoformat()
                data[key] = metrics_dict
            
            with open(self.font_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.font_metrics)} font metrics to cache")
        except Exception as e:
            logger.error(f"Could not save font metrics: {e}")
    
    def record_font_usage(self, font_family: str, font_weight: int, load_time: float = 0.0):
        """Record font usage for analytics"""
        key = f"{font_family}_{font_weight}"
        now = datetime.now()
        
        if key in self.font_metrics:
            metrics = self.font_metrics[key]
            metrics.usage_count += 1
            metrics.last_used = now
            if load_time > 0:
                metrics.load_time = (metrics.load_time + load_time) / 2
        else:
            self.font_metrics[key] = FontMetrics(
                font_family=font_family,
                font_weight=font_weight,
                usage_count=1,
                load_time=load_time,
                file_size=0,  # Will be updated if available
                last_used=now,
                performance_score=1.0,
                accessibility_score=1.0
            )
        
        # Save metrics periodically
        if len(self.font_metrics) % 10 == 0:
            self.save_font_metrics()
    
    def get_font_performance_stats(self) -> Dict:
        """Get font performance statistics"""
        if not self.font_metrics:
            return {"message": "No font metrics available"}
        
        total_usage = sum(m.usage_count for m in self.font_metrics.values())
        avg_load_time = sum(m.load_time for m in self.font_metrics.values()) / len(self.font_metrics)
        
        most_used = max(self.font_metrics.values(), key=lambda x: x.usage_count)
        fastest_loading = min(self.font_metrics.values(), key=lambda x: x.load_time)
        
        return {
            "total_fonts": len(self.font_metrics),
            "total_usage": total_usage,
            "average_load_time": round(avg_load_time, 3),
            "most_used_font": f"{most_used.font_family} {most_used.font_weight} ({most_used.usage_count} times)",
            "fastest_loading": f"{fastest_loading.font_family} {fastest_loading.font_weight} ({fastest_loading.load_time}s)",
            "recent_usage": len([m for m in self.font_metrics.values() 
                               if m.last_used > datetime.now() - timedelta(hours=24)])
        }
    
    def get_font_recommendations(self, use_case: Optional[str] = None) -> Dict:
        """Get font recommendations for specific use cases"""
        if use_case:
            if use_case in self.recommendations:
                return asdict(self.recommendations[use_case])
            else:
                return {"error": f"Unknown use case: {use_case}"}
        
        return {
            "recommendations": {k: asdict(v) for k, v in self.recommendations.items()},
            "summary": {
                "primary_font": "Inter",
                "reasoning": "Inter provides excellent readability, modern appearance, and consistent rendering across all devices",
                "performance_benefits": "Optimized loading with font-display: swap, preloaded critical weights",
                "accessibility_benefits": "High contrast ratios, clear character shapes, excellent screen reader support"
            }
        }
    
    def generate_font_css(self, optimize_performance: bool = True) -> str:
        """Generate optimized font CSS"""
        css_parts = []
        
        # Font face declarations with optimization
        if optimize_performance:
            css_parts.append("""
/* Optimized Font Loading */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuI6fAZ9hiA.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuGKYAZ9hiA.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuFuYAZ9hiA.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
""")
        
        # CSS Variables
        css_parts.append("""
/* Font Variables */
:root {
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-extrabold: 800;
}
""")
        
        return "\n".join(css_parts)
    
    def analyze_font_accessibility(self, font_family: str) -> Dict:
        """Analyze font accessibility characteristics"""
        accessibility_scores = {
            "Inter": {
                "readability": 9.5,
                "contrast": 9.0,
                "screen_reader": 10.0,
                "dyslexia_friendly": 8.5,
                "overall_score": 9.2,
                "strengths": [
                    "Excellent character distinction",
                    "High contrast ratios",
                    "Clear letterforms",
                    "Consistent spacing"
                ],
                "recommendations": [
                    "Use minimum 16px for body text",
                    "Maintain 1.5 line height",
                    "Use 400-600 weights for best readability"
                ]
            },
            "SF Mono": {
                "readability": 8.0,
                "contrast": 8.5,
                "screen_reader": 9.0,
                "dyslexia_friendly": 7.0,
                "overall_score": 8.1,
                "strengths": [
                    "Consistent character width",
                    "Clear distinction between similar characters",
                    "Good for code and data"
                ],
                "recommendations": [
                    "Use only for code and technical data",
                    "Avoid for body text",
                    "Use 400 weight only"
                ]
            }
        }
        
        return accessibility_scores.get(font_family, {
            "readability": 7.0,
            "contrast": 7.0,
            "screen_reader": 8.0,
            "dyslexia_friendly": 6.0,
            "overall_score": 7.0,
            "strengths": ["Standard accessibility"],
            "recommendations": ["Consider using Inter for better accessibility"]
        })
    
    def get_font_loading_strategy(self) -> Dict:
        """Get recommended font loading strategy"""
        return {
            "strategy": "Critical CSS with font-display: swap",
            "implementation": {
                "preload_critical": ["Inter 400", "Inter 500", "Inter 600"],
                "font_display": "swap",
                "unicode_range": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
                "format": "woff2"
            },
            "performance_benefits": [
                "Reduces layout shift with font-display: swap",
                "Preloads critical fonts for faster rendering",
                "Uses WOFF2 format for smaller file sizes",
                "Unicode range optimization reduces download size"
            ],
            "fallback_strategy": {
                "primary": "Inter",
                "fallbacks": ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial"],
                "reasoning": "System fonts provide immediate rendering while custom fonts load"
            }
        }
    
    def cleanup_old_metrics(self, days: int = 30):
        """Clean up old font metrics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_keys = [
            key for key, metrics in self.font_metrics.items()
            if metrics.last_used < cutoff_date and metrics.usage_count < 5
        ]
        
        for key in old_keys:
            del self.font_metrics[key]
        
        if old_keys:
            self.save_font_metrics()
            logger.info(f"Cleaned up {len(old_keys)} old font metrics")
    
    def get_service_stats(self) -> Dict:
        """Get service statistics"""
        return {
            "service": "Font Optimization Service",
            "version": "1.0.0",
            "metrics_count": len(self.font_metrics),
            "recommendations_count": len(self.recommendations),
            "cache_file": self.font_cache_file,
            "last_cleanup": "Auto-cleanup every 30 days",
            "features": [
                "Font performance tracking",
                "Accessibility analysis",
                "Loading optimization",
                "Usage analytics",
                "Recommendation engine"
            ]
        } 