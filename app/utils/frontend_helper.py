"""
Utility function to serve React frontend for SPA routing
Replaces hardcoded localhost:3000 redirects
"""
import os
from flask import send_from_directory, redirect


def get_frontend_dist_path():
    """Get the path to the frontend dist directory"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
    if not os.path.exists(frontend_dist):
        frontend_dist = os.path.join(base_dir, 'frontend', 'dist_prod')
    return frontend_dist


def serve_frontend(fallback_path='/'):
    """
    Serve React frontend index.html for SPA routing.
    This allows React Router to handle client-side routing.
    
    Args:
        fallback_path: Path to redirect to if index.html doesn't exist
        
    Returns:
        Flask response with index.html or redirect
    """
    frontend_dist = get_frontend_dist_path()
    index_path = os.path.join(frontend_dist, 'index.html')
    
    if os.path.exists(index_path):
        response = send_from_directory(frontend_dist, 'index.html')
        # Disable caching for index.html to ensure fresh content
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        # Fallback to relative redirect
        return redirect(fallback_path)

