# -*- coding: utf-8 -*-
"""
JWT Authentication Module
Provides JWT token generation, validation, and password hashing
"""

import hashlib
import hmac
import json
import time
import os
import sqlite3
from typing import Optional, Tuple, Dict, Any

# JWT Configuration
JWT_SECRET = "digital-company-secret-key-2024"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY = 86400 * 7  # 7 days in seconds

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db', 'company.db')


def _get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _base64url_encode(data: bytes) -> str:
    """Base64 URL-safe encoding"""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _base64url_decode(data: str) -> bytes:
    """Base64 URL-safe decoding"""
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash password using SHA-256 with salt
    Returns: (hash, salt)
    """
    if salt is None:
        salt = os.urandom(16).hex()
    
    # Create hash with salt
    password_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    # Use PBKDF2-like approach with multiple iterations
    hash_obj = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, iterations=100000)
    hash_hex = hash_obj.hex()
    
    return hash_hex, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify password against hash
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def create_token(user_id: int, username: str, role: str) -> str:
    """
    Create JWT token
    """
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + TOKEN_EXPIRY
    }
    
    # Header
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    
    # Payload
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    # Signature
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).hexdigest()
    signature_b64 = _base64url_encode(signature.encode('utf-8'))
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token
    Returns payload if valid, None if invalid/expired
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_signature = hmac.new(
            JWT_SECRET.encode('utf-8'), 
            message, 
            hashlib.sha256
        ).hexdigest()
        expected_signature_b64 = _base64url_encode(expected_signature.encode('utf-8'))
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
        
        # Decode payload
        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if payload.get('exp', 0) < int(time.time()):
            return None
        
        return payload
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with username and password
    Returns user info if authenticated, None otherwise
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, username, password_hash, salt, role FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        user_id = row['id']
        stored_hash = row['password_hash']
        salt = row['salt']
        role = row['role']
        
        if verify_password(password, stored_hash, salt):
            return {
                "id": user_id,
                "username": row['username'],
                "role": role
            }
        return None
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row['id'],
                "username": row['username'],
                "role": row['role']
            }
        return None
    finally:
        conn.close()


def create_user(username: str, password: str, role: str = "user") -> Optional[int]:
    """Create a new user"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash, salt = hash_password(password)
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, salt, role)
        )
        conn.commit()
        
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # Username already exists
    except Exception as e:
        print(f"Create user error: {e}")
        return None
    finally:
        conn.close()


# Token storage for logout (in production, use Redis or database)
_token_blacklist = set()


def blacklist_token(token: str):
    """Add token to blacklist (for logout)"""
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in _token_blacklist


# Decorator for protected routes
def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            return jsonify({"success": False, "error": "No token provided"}), 401
        
        if is_token_blacklisted(token):
            return jsonify({"success": False, "error": "Token has been revoked"}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401
        
        # Store user info in request context
        request.user = payload
        
        return f(*args, **kwargs)
    
    return decorated


# Initialize default admin user if not exists
def init_default_users():
    """Initialize default admin user"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Create default admin user
            password_hash, salt = hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                ("admin", password_hash, salt, "admin")
            )
            conn.commit()
            print("[OK] Default admin user created (admin/admin123)")
    finally:
        conn.close()


if __name__ == "__main__":
    # Test the module
    print("Testing JWT Auth Module...")
    
    # Initialize default users
    init_default_users()
    
    # Test password hashing
    pwd = "test123"
    hash_val, salt = hash_password(pwd)
    print(f"Password: {pwd}")
    print(f"Hash: {hash_val}")
    print(f"Salt: {salt}")
    print(f"Verify: {verify_password(pwd, hash_val, salt)}")
    
    # Test token creation
    token = create_token(1, "admin", "admin")
    print(f"\nToken: {token[:50]}...")
    
    # Test token verification
    payload = verify_token(token)
    print(f"Payload: {payload}")
