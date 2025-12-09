import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv('JWT_Secret', os.getenv('Secret_Key'))
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # 1 hour


def generate_access_token(user_id, email):
    """Generate a JWT access token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'access',
        'exp': datetime.utcnow() + ACCESS_TOKEN_EXPIRY,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def verify_token(token, token_type='access'):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        
        # Verify token type
        if payload.get('type') != token_type:
            return None, "Invalid token type"
        
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def get_token_from_header():
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        # Support both "Bearer <token>" and just "<token>"
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return auth_header
    except:
        return None


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        payload, error = verify_token(token, token_type='access')
        
        if error:
            return jsonify({"error": error}), 401
        
        # Add user info to request context
        request.current_user_id = payload.get('user_id')
        request.current_user_email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated

