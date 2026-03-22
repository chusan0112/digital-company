# -*- coding: utf-8 -*-
"""
Flask-based Digital Company Server
With JWT Authentication
"""
import sys
import os

os.chdir(r'C:\Users\Administrator\.openclaw\skills\digital-company')
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\skills\digital-company')

from flask import Flask, jsonify, request, send_from_directory
from company import get_company

# Import auth module
from auth.jwt_auth import (
    create_token, verify_token, authenticate_user,
    blacklist_token, is_token_blacklisted, init_default_users,
    require_auth
)

app = Flask(__name__)

# Initialize default users on startup
init_default_users()


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ============== Authentication Endpoints ==============

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login - returns JWT token"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({
            "success": False, 
            "error": "Username and password are required"
        }), 400
    
    # Authenticate user
    user = authenticate_user(username, password)
    
    if not user:
        return jsonify({
            "success": False, 
            "error": "Invalid username or password"
        }), 401
    
    # Create JWT token
    token = create_token(user['id'], user['username'], user['role'])
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout - blacklists the token"""
    # Get token from header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        blacklist_token(token)
    
    return jsonify({
        "success": True,
        "message": "Logout successful"
    })


@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify():
    """Verify token - returns user info if valid"""
    user = request.user
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.get('user_id'),
            "username": user.get('username'),
            "role": user.get('role')
        }
    })


# ============== Public API Endpoints ==============

@app.route('/api/dashboard')
def dashboard():
    return jsonify(get_company().get_dashboard())


@app.route('/api/employees')
def employees():
    return jsonify([e.__dict__ for e in get_company().list_employees()])


@app.route('/api/departments')
def departments():
    return jsonify([d.__dict__ for d in get_company().list_departments()])


@app.route('/api/projects')
def projects():
    return jsonify([p.__dict__ for p in get_company().list_projects()])


@app.route('/api/tasks')
def tasks():
    return jsonify([t.__dict__ for t in get_company().list_tasks()])


@app.route('/api/governance')
def governance():
    return jsonify([])


# ============== Protected API Endpoints ==============

@app.route('/api/protected/dashboard', methods=['GET'])
@require_auth
def protected_dashboard():
    """Protected dashboard endpoint"""
    return jsonify({
        "success": True,
        "data": get_company().get_dashboard(),
        "user": request.user
    })


@app.route('/api/protected/employees', methods=['GET'])
@require_auth
def protected_employees():
    """Protected employees endpoint"""
    return jsonify({
        "success": True,
        "data": [e.__dict__ for e in get_company().list_employees()],
        "user": request.user
    })


# ============== Health Check ==============

@app.route('/api/health')
def health():
    return jsonify({
        "success": True,
        "service": "digital-company",
        "status": "ok",
        "auth_enabled": True
    })


if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:8080")
    print("Authentication enabled")
    print("Default admin credentials: admin / admin123")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
