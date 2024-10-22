import functools
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Register a new user
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Expect JSON payload
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    error = None

    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'

    if error is None:
        try:
            db.execute(
                "INSERT INTO user (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except db.IntegrityError:
            error = f"User {username} is already registered."
        else:
            return jsonify({"message": "User registered successfully."}), 201

    return jsonify({"error": error}), 400

# Log in an existing user
@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Expect JSON payload
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    error = None
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        error = 'Incorrect username or password.'
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password or username.'

    if error is None:
        # Create a JWT token valid for 1 hour
        access_token = create_access_token(identity=user['id'])
        return jsonify(access_token=access_token), 200

    return jsonify({"error": error}), 400

# Logout route (not needed with JWT but you can use this to invalidate tokens if needed)
@bp.route('/logout', methods=['POST'])
def logout():
    # With JWT, you don't have sessions to clear, but you could implement token revoking here.
    return jsonify({"message": "Logout successful."}), 200

# Example route protected with JWT
@bp.route('/protected', methods=['GET'])
@jwt_required()  # Use jwt_required to protect routes
def protected():
    current_user_id = get_jwt_identity()  # Get the user ID from the JWT token
    return jsonify(logged_in_as=current_user_id), 200

# Old login_required decorator replaced with jwt_required()
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        return jsonify({"error": "Login required."}), 401
    return wrapped_view
