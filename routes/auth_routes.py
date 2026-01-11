"""
Authentication Routes for Universal Business Automation
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import jwt
from functools import wraps
from models.user import User
from extensions import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
            
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            secret_key = current_app.config.get('JWT_SECRET_KEY', 'dev-key-change-in-production-123')
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            current_user = User.query.get(data['id'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Failed to validate token'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
        
    # Create new user
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(
        email=data['email'],
        password=hashed_password,
        credits=10,  # Initial credits for new users
        is_admin=False
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # Generate token
    token = jwt.encode({
        'id': new_user.id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, current_app.config.get('JWT_SECRET_KEY', 'dev-key-change-in-production-123'))
    
    return jsonify({
        'token': token,
        'user': {
            'id': new_user.id,
            'email': new_user.email,
            'credits': new_user.credits,
            'is_admin': new_user.is_admin
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return token"""
    try:
        if not request.is_json:
            print("Error: Request is not JSON")
            return jsonify({'message': 'Request must be JSON'}), 400
            
        data = request.get_json()
        print(f"Login attempt for email: {data.get('email')}")
        
        if 'email' not in data or 'password' not in data:
            print("Error: Missing email or password in request")
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        print(f"User found: {user is not None}")
        
        if not user:
            print("Login failed: User not found")
            return jsonify({'message': 'Invalid credentials'}), 401
        
        print(f"Checking password for user: {user.email}")
        if not hasattr(user, 'check_password'):
            print("Error: User model is missing check_password method")
            return jsonify({'message': 'Server configuration error'}), 500
            
        if not user.check_password(data['password']):
            print("Login failed: Invalid password")
            return jsonify({'message': 'Invalid credentials'}), 401
        
        print(f"Using JWT_SECRET_KEY: {'Set' if current_app.config.get('JWT_SECRET_KEY') else 'Not set'}")
        token = jwt.encode({
            'id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, current_app.config.get('JWT_SECRET_KEY', 'dev-key-change-in-production-123'))
        
        print("Login successful")
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'credits': user.credits,
                'is_admin': user.is_admin
            }
        })
        
    except jwt.PyJWTError as e:
        print(f"JWT Error: {str(e)}")
        return jsonify({'message': 'Error generating authentication token'}), 500
    except Exception as e:
        print(f"Unexpected error during login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'An unexpected error occurred during login'}), 500
