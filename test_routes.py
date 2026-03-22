# Test script to check routes
from flask import Flask
app = Flask(__name__)

# Import and register lifecycle endpoints
from domains.project_lifecycle_service import get_lifecycle_service

# Simulate the routes from dashboard_server.py
lifecycle = get_lifecycle_service()

@app.route('/api/lifecycle/projects', methods=['GET'])
def api_list_projects():
    projects = lifecycle.list_projects()
    return {"success": True, "projects": projects}

# Print all routes
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} {list(rule.methods)}")
