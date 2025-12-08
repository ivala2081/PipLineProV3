"""
Responsive Automation Service
Automatically handles responsive design for all UI elements
Including typography scaling, component resizing, and viewport adjustments
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from flask import current_app, render_template_string
import re

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = logging.getLogger(__name__)

class ResponsiveAutomationService:
    """Service for automating responsive design across the application"""
    
    def __init__(self):
        self.breakpoints = {
            'xs': 480,
            'sm': 576,
            'md': 768,
            'lg': 992,
            'xl': 1200,
            '2xl': 1400
        }
        
        self.fluid_scaling_config = {
            'typography': {
                'base_font_size': 16,
                'scale_factor': 1.2,
                'min_scale': 0.8,
                'max_scale': 1.5
            },
            'spacing': {
                'base_spacing': 16,
                'scale_factor': 1.1,
                'min_scale': 0.7,
                'max_scale': 1.3
            },
            'components': {
                'button_height': 44,
                'input_height': 44,
                'card_padding': 16,
                'icon_size': 20
            }
        }
        
        self.responsive_templates = {}
        self.dynamic_css_cache = {}
        self.last_generation = None
        
    def generate_responsive_css(self, viewport_width: int = 1200) -> str:
        """
        Generate dynamic CSS based on viewport width
        
        Args:
            viewport_width: Target viewport width for scaling
            
        Returns:
            Generated CSS string
        """
        try:
            # Calculate scaling factors
            scale_factor = self._calculate_scale_factor(viewport_width)
            
            # Generate fluid CSS variables
            css_variables = self._generate_fluid_variables(scale_factor)
            
            # Generate responsive utilities
            responsive_utilities = self._generate_responsive_utilities()
            
            # Generate component styles
            component_styles = self._generate_component_styles(scale_factor)
            
            # Combine all CSS
            css = f"""
/* ===== DYNAMIC RESPONSIVE CSS ===== */
/* Generated on: {datetime.now().isoformat()} */
/* Viewport width: {viewport_width}px */
/* Scale factor: {scale_factor:.3f} */

{css_variables}

{responsive_utilities}

{component_styles}

/* ===== PERFORMANCE OPTIMIZATIONS ===== */
* {{
  box-sizing: border-box;
}}

/* Optimize paint and layout */
.card, .btn, .form-input {{
  will-change: transform;
  backface-visibility: hidden;
}}

/* Smooth animations */
.sidebar, .modal, .navbar-collapse {{
  will-change: transform;
  transition: transform 0.3s ease;
}}

/* ===== ACCESSIBILITY IMPROVEMENTS ===== */
@media (max-width: 768px) {{
  .btn, .nav-link, .form-check-input {{
    min-height: 44px;
    min-width: 44px;
  }}
  
  .form-input, .form-control {{
    min-height: 44px;
  }}
}}

/* ===== PRINT STYLES ===== */
@media print {{
  .sidebar, .navbar, .btn, .modal {{
    display: none !important;
  }}
  
  .main-content {{
    margin: 0 !important;
    width: 100% !important;
    padding: 0 !important;
  }}
  
  .card, .glass-card {{
    box-shadow: none !important;
    border: 1px solid #000 !important;
  }}
}}
"""
            
            return css.strip()
            
        except Exception as e:
            logger.error(f"Error generating responsive CSS: {e}")
            return ""
    
    def _calculate_scale_factor(self, viewport_width: int) -> float:
        """Calculate scaling factor based on viewport width"""
        base_width = 1200
        scale_factor = viewport_width / base_width
        
        # Apply min/max constraints
        min_scale = self.fluid_scaling_config['typography']['min_scale']
        max_scale = self.fluid_scaling_config['typography']['max_scale']
        
        return max(min_scale, min(max_scale, scale_factor))
    
    def _generate_fluid_variables(self, scale_factor: float) -> str:
        """Generate fluid CSS variables"""
        typography_config = self.fluid_scaling_config['typography']
        spacing_config = self.fluid_scaling_config['spacing']
        
        # Calculate fluid typography
        base_font_size = typography_config['base_font_size']
        fluid_text_sizes = {}
        
        for i, size_name in enumerate(['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl']):
            base_size = base_font_size * (0.75 + i * 0.25)
            fluid_size = base_size * scale_factor
            fluid_text_sizes[f'--fluid-text-{size_name}'] = f"{fluid_size:.2f}px"
        
        # Calculate fluid spacing
        base_spacing = spacing_config['base_spacing']
        fluid_spacing = {}
        
        for i, space_name in enumerate(['xs', 'sm', 'md', 'lg', 'xl', '2xl']):
            base_space = base_spacing * (0.25 + i * 0.5)
            fluid_space = base_space * scale_factor
            fluid_spacing[f'--fluid-space-{space_name}'] = f"{fluid_space:.2f}px"
        
        # Generate CSS variables
        css_variables = ":root {\n"
        
        for var_name, value in fluid_text_sizes.items():
            css_variables += f"  {var_name}: {value};\n"
        
        for var_name, value in fluid_spacing.items():
            css_variables += f"  {var_name}: {value};\n"
        
        # Add component variables with proper naming
        components_config = self.fluid_scaling_config['components']
        for component_name, base_value in components_config.items():
            fluid_value = base_value * scale_factor
            # Map component names to CSS variable names
            if component_name == 'button_height':
                css_variables += f"  --fluid-button-height: {fluid_value:.2f}px;\n"
            elif component_name == 'input_height':
                css_variables += f"  --fluid-input-height: {fluid_value:.2f}px;\n"
            elif component_name == 'card_padding':
                css_variables += f"  --fluid-card-padding: {fluid_value:.2f}px;\n"
            elif component_name == 'icon_size':
                css_variables += f"  --fluid-icon-size: {fluid_value:.2f}px;\n"
            else:
                css_variables += f"  --fluid-{component_name}: {fluid_value:.2f}px;\n"
        
        css_variables += "}"
        
        return css_variables
    
    def _generate_responsive_utilities(self) -> str:
        """Generate responsive utility classes"""
        utilities = []
        
        # Generate display utilities for each breakpoint
        for breakpoint, width in self.breakpoints.items():
            utilities.append(f"""
/* {breakpoint.upper()} breakpoint ({width}px) */
@media (min-width: {width}px) {{
  .d-{breakpoint}-none {{ display: none !important; }}
  .d-{breakpoint}-block {{ display: block !important; }}
  .d-{breakpoint}-flex {{ display: flex !important; }}
  .d-{breakpoint}-inline {{ display: inline !important; }}
  .d-{breakpoint}-inline-block {{ display: inline-block !important; }}
  
  .text-{breakpoint}-left {{ text-align: left !important; }}
  .text-{breakpoint}-center {{ text-align: center !important; }}
  .text-{breakpoint}-right {{ text-align: right !important; }}
  
  .justify-content-{breakpoint}-start {{ justify-content: flex-start !important; }}
  .justify-content-{breakpoint}-center {{ justify-content: center !important; }}
  .justify-content-{breakpoint}-end {{ justify-content: flex-end !important; }}
  .justify-content-{breakpoint}-between {{ justify-content: space-between !important; }}
  
  .align-items-{breakpoint}-start {{ align-items: flex-start !important; }}
  .align-items-{breakpoint}-center {{ align-items: center !important; }}
  .align-items-{breakpoint}-end {{ align-items: flex-end !important; }}
}}""")
        
        return "\n".join(utilities)
    
    def _generate_component_styles(self, scale_factor: float) -> str:
        """Generate responsive component styles"""
        components_config = self.fluid_scaling_config['components']
        
        styles = []
        
        # Button styles
        button_height = components_config['button_height'] * scale_factor
        styles.append(f"""
.btn, .login-btn {{
  min-height: {button_height:.2f}px;
  padding: calc(var(--fluid-space-sm) * {scale_factor:.3f}) calc(var(--fluid-space-md) * {scale_factor:.3f});
  font-size: var(--fluid-text-base);
  border-radius: calc(var(--business-radius-lg) * {scale_factor:.3f});
}}""")
        
        # Form input styles
        input_height = components_config['input_height'] * scale_factor
        styles.append(f"""
.form-input, .form-control {{
  min-height: {input_height:.2f}px;
  padding: calc(var(--fluid-space-sm) * {scale_factor:.3f}) calc(var(--fluid-space-md) * {scale_factor:.3f});
  font-size: var(--fluid-text-base);
  border-radius: calc(var(--business-radius-lg) * {scale_factor:.3f});
}}""")
        
        # Card styles
        card_padding = components_config['card_padding'] * scale_factor
        styles.append(f"""
.card, .glass-card, .metric-card {{
  padding: {card_padding:.2f}px;
  border-radius: calc(var(--business-radius-lg) * {scale_factor:.3f});
  margin-bottom: calc(var(--fluid-space-md) * {scale_factor:.3f});
}}""")
        
        # Icon styles
        icon_size = components_config['icon_size'] * scale_factor
        styles.append(f"""
.bi, .icon {{
  font-size: {icon_size:.2f}px;
}}

.icon-sm {{ font-size: {icon_size * 0.8:.2f}px; }}
.icon-lg {{ font-size: {icon_size * 1.2:.2f}px; }}
.icon-xl {{ font-size: {icon_size * 1.5:.2f}px; }}""")
        
        return "\n".join(styles)
    
    def process_template_responsiveness(self, template_content: str, context: Dict = None) -> str:
        """
        Process template content to add responsive classes and attributes
        
        Args:
            template_content: Raw template content
            context: Template context variables
            
        Returns:
            Processed template content
        """
        try:
            if context is None:
                context = {}
            
            # Add responsive classes to common elements
            processed_content = self._add_responsive_classes(template_content)
            
            # Add responsive attributes
            processed_content = self._add_responsive_attributes(processed_content)
            
            # Add responsive data attributes
            processed_content = self._add_responsive_data_attributes(processed_content)
            
            # Process responsive images
            processed_content = self._process_responsive_images(processed_content)
            
            # Add responsive JavaScript hooks
            processed_content = self._add_responsive_js_hooks(processed_content)
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error processing template responsiveness: {e}")
            return template_content
    
    def _add_responsive_classes(self, content: str) -> str:
        """Add responsive classes to HTML elements"""
        # Add responsive classes to buttons
        content = re.sub(
            r'<button([^>]*class="[^"]*)([^"]*)"([^>]*)>',
            r'<button\1\2 btn-responsive" data-responsive="true"\3>',
            content
        )
        
        # Add responsive classes to forms
        content = re.sub(
            r'<form([^>]*class="[^"]*)([^"]*)"([^>]*)>',
            r'<form\1\2 form-responsive" data-responsive="true"\3>',
            content
        )
        
        # Add responsive classes to cards
        content = re.sub(
            r'<div([^>]*class="[^"]*card[^"]*)([^"]*)"([^>]*)>',
            r'<div\1\2 card-responsive" data-responsive="true"\3>',
            content
        )
        
        # Add responsive classes to inputs
        content = re.sub(
            r'<input([^>]*class="[^"]*form-input[^"]*)([^"]*)"([^>]*)>',
            r'<input\1\2 input-responsive" data-responsive="true"\3>',
            content
        )
        
        return content
    
    def _add_responsive_attributes(self, content: str) -> str:
        """Add responsive attributes to HTML elements"""
        # Add viewport meta tag if not present
        if '<meta name="viewport"' not in content:
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">'
            content = content.replace('</head>', f'{viewport_meta}\n</head>')
        
        # Add responsive data attributes
        content = re.sub(
            r'<body([^>]*)>',
            r'<body\1 data-responsive="true" data-breakpoint="lg">',
            content
        )
        
        return content
    
    def _add_responsive_data_attributes(self, content: str) -> str:
        """Add responsive data attributes for JavaScript"""
        # Add data attributes for responsive automation
        responsive_elements = [
            'button', 'input', 'select', 'textarea', 'div', 'section', 'article'
        ]
        
        for element in responsive_elements:
            content = re.sub(
                rf'<{element}([^>]*class="[^"]*)([^"]*)"([^>]*)>',
                rf'<{element}\1\2" data-responsive-element="{element}"\3>',
                content
            )
        
        return content
    
    def _process_responsive_images(self, content: str) -> str:
        """Process images for responsive behavior"""
        # Add lazy loading to images
        content = re.sub(
            r'<img([^>]*src="[^"]*)([^"]*)"([^>]*)>',
            r'<img\1\2" loading="lazy" data-responsive="true"\3>',
            content
        )
        
        # Add responsive image classes
        content = re.sub(
            r'<img([^>]*class="[^"]*)([^"]*)"([^>]*)>',
            r'<img\1\2 img-fluid" data-responsive="true"\3>',
            content
        )
        
        return content
    
    def _add_responsive_js_hooks(self, content: str) -> str:
        """Add JavaScript hooks for responsive behavior"""
        # Add responsive automation script if not present
        if 'responsive-automation.js' not in content:
            script_tag = '<script src="{{ url_for(\'static\', filename=\'js/responsive-automation.js\') }}"></script>'
            content = content.replace('</body>', f'{script_tag}\n</body>')
        
        # Add responsive initialization
        init_script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    if (window.responsiveAutomation) {
        // Initialize responsive automation
        window.responsiveAutomation.updateResponsiveClasses();
        window.responsiveAutomation.updateFluidScaling();
    }
});
</script>"""
        
        content = content.replace('</body>', f'{init_script}\n</body>')
        
        return content
    
    def generate_responsive_template(self, template_name: str, context: Dict = None) -> str:
        """
        Generate a responsive version of a template
        
        Args:
            template_name: Name of the template to process
            context: Template context variables
            
        Returns:
            Processed template content
        """
        try:
            # Get template content
            template_content = self._get_template_content(template_name)
            
            if not template_content:
                logger.warning(f"Template {template_name} not found")
                return ""
            
            # Process template for responsiveness
            processed_content = self.process_template_responsiveness(template_content, context)
            
            # Cache the processed template
            self.responsive_templates[template_name] = {
                'content': processed_content,
                'timestamp': datetime.now(),
                'context': context
            }
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error generating responsive template {template_name}: {e}")
            return ""
    
    def _get_template_content(self, template_name: str) -> str:
        """Get template content from file system"""
        try:
            template_path = os.path.join(current_app.root_path, 'templates', template_name)
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error reading template {template_name}: {e}")
            return ""
    
    def get_responsive_css_url(self, viewport_width: int = 1200) -> str:
        """
        Get URL for responsive CSS file
        
        Args:
            viewport_width: Target viewport width
            
        Returns:
            CSS file URL
        """
        try:
            # Generate CSS if not cached or outdated
            cache_key = f"responsive_css_{viewport_width}"
            
            if (cache_key not in self.dynamic_css_cache or 
                self.last_generation is None or 
                (datetime.now() - self.last_generation).seconds > 300):  # 5 minutes cache
                
                css_content = self.generate_responsive_css(viewport_width)
                self.dynamic_css_cache[cache_key] = css_content
                self.last_generation = datetime.now()
            
            # Save CSS to file
            css_filename = f"responsive_{viewport_width}.css"
            css_path = os.path.join(current_app.root_path, 'static', 'css', css_filename)
            
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(self.dynamic_css_cache[cache_key])
            
            return f"/static/css/{css_filename}"
            
        except Exception as e:
            logger.error(f"Error generating responsive CSS URL: {e}")
            return ""
    
    def get_responsive_config(self) -> Dict:
        """Get responsive configuration for frontend"""
        return {
            'breakpoints': self.breakpoints,
            'fluid_scaling': self.fluid_scaling_config,
            'current_breakpoint': 'lg',  # Default
            'viewport_width': 1200,     # Default
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True
        }
    
    def update_responsive_config(self, config: Dict) -> bool:
        """
        Update responsive configuration
        
        Args:
            config: New configuration dictionary
            
        Returns:
            Success status
        """
        try:
            if 'breakpoints' in config:
                self.breakpoints.update(config['breakpoints'])
            
            if 'fluid_scaling' in config:
                self.fluid_scaling_config.update(config['fluid_scaling'])
            
            # Clear cache to force regeneration
            self.dynamic_css_cache.clear()
            self.last_generation = None
            
            logger.info("Responsive configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating responsive configuration: {e}")
            return False
    
    def get_responsive_stats(self) -> Dict:
        """Get responsive automation statistics"""
        return {
            'templates_processed': len(self.responsive_templates),
            'css_cache_size': len(self.dynamic_css_cache),
            'last_generation': self.last_generation.isoformat() if self.last_generation else None,
            'breakpoints': self.breakpoints,
            'config': self.fluid_scaling_config
        }
    
    def cleanup_cache(self) -> bool:
        """Clean up cached data"""
        try:
            self.dynamic_css_cache.clear()
            self.responsive_templates.clear()
            self.last_generation = None
            
            logger.info("Responsive cache cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up responsive cache: {e}")
            return False

# Global instance
responsive_automation_service = ResponsiveAutomationService() 