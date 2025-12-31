import os
from app import create_app

print(f"Current working directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print(f"dirname(__file__): {os.path.dirname(__file__)}")

app = create_app()

# Check frontend_dist path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"base_dir (from __file__): {base_dir}")

frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
print(f"frontend_dist: {frontend_dist}")
print(f"frontend_dist exists: {os.path.exists(frontend_dist)}")

index_path = os.path.join(frontend_dist, 'index.html')
print(f"index_path: {index_path}")
print(f"index_path exists: {os.path.exists(index_path)}")

