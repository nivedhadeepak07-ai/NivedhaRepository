from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ===== CONFIGURATION =====
# In production, use environment variables and never commit secrets
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this to a strong secret
JWT_EXPIRATION_HOURS = 24

# ===== MOCK USER DATABASE =====
# This is for demonstration purposes only
# In production, use a real database (PostgreSQL, MongoDB, etc.) with hashed passwords
# MOCK USER DATABASE WITH FULL INFO
MOCK_USERS = {
    "student1": {
        "password": "password123",
        "email": "student1@college.edu",
        "enrollment_date": "2023-09-01",
        "status": "Active",
        "courses": ["CS 101", "MATH 101", "PHYS 101"],
        "gpa": 3.8
    },
    "student2": {
        "password": "securepass456",
        "email": "student2@college.edu",
        "enrollment_date": "2022-09-01",
        "status": "Active",
        "courses": ["ENG 101", "BIO 101", "CHEM 101"],
        "gpa": 3.4
    },
    "alice": {
        "password": "alice123",
        "email": "alice@college.edu",
        "enrollment_date": "2021-09-01",
        "status": "Inactive",
        "courses": ["HIST 101", "PHIL 101", "ART 101"],
        "gpa": 3.9
    }
}



# ===== JWT AUTHENTICATION MIDDLEWARE =====
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow OPTIONS requests without authentication (CORS preflight)
        if request.method == "OPTIONS":
            return "", 204
        
        token = None

        # JWT expected in Authorization header: "Bearer <token>"
        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Token format invalid"}), 401

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = data.get("username")

            if not username or username not in MOCK_USERS:
                return jsonify({"message": "User not found"}), 401

            # Pass username and full user dict
            current_user = MOCK_USERS[username]

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(username, current_user, *args, **kwargs)

    return decorated

# ===== ROUTES =====

@app.route("/api/login", methods=["POST"])
def login():
    """
    Login endpoint - Authenticates user and returns JWT token
    
    Request body: { "username": "student1", "password": "password123" }
    Response: { "token": "<jwt_token>", "message": "Login successful" }
    
    How it works:
    1. Extract username and password from request
    2. Check credentials against mock database
    3. If valid, create JWT token with expiration
    4. Return token to client
    """
    data = request.get_json()
    
    # Validate request contains username and password
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "Missing username or password"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    # Check credentials (in production, compare with hashed password)
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"message": "Invalid credentials"}), 401

    
    # ===== JWT TOKEN CREATION =====
    # Create payload (data stored in the token)
    payload = {
        "username": username,
        "iat": datetime.utcnow(),  # Issued at time
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)  # Expiration time
    }
    
    # Encode token using SECRET_KEY
    # The token is signed with HS256 algorithm, making it cryptographically secure
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        "token": token,
        "username": username,
        "message": "Login successful"
    }), 200


@app.route("/api/dashboard", methods=["GET", "OPTIONS"])
@token_required
def dashboard(username, current_user):
    return jsonify({
        "message": f"Welcome, {username}!",
        "data": {
            "username": username,
            "courses": current_user["courses"],
            "gpa": current_user["gpa"]
        }
    }), 200


@app.route("/api/profile", methods=["GET", "OPTIONS"])
@token_required
def profile(username, current_user):
    return jsonify({
        "username": username,
        "email": current_user["email"],
        "enrollment_date": current_user.get("enrollment_date", "N/A"),
        "status": current_user.get("status", "Active"),
        "courses": current_user.get("courses", []),
        "gpa": current_user.get("gpa", "N/A"),
        "standing": "Good",
        "credits": "120"
    }), 200


@app.route("/api/logout", methods=["POST"])
@token_required
def logout(username, current_user):
    """
    Logout endpoint
    
    Note: JWT tokens cannot be invalidated on the server side by default.
    This is why token expiration is important.
    
    For production, implement token blacklist:
    - Store invalidated tokens in a database or Redis
    - Check blacklist in @token_required decorator
    
    For now, client just deletes the token from localStorage
    """
    return jsonify({
        "message": f"Goodbye, {username}!",
        "status": "logged_out"
    }), 200


@app.route("/api/public", methods=["GET"])
def public():
    """
    Public endpoint - No authentication required
    """
    return jsonify({
        "message": "This is a public endpoint",
        "data": "Anyone can access this"
    }), 200


@app.route("/", methods=["GET"])
def index():
    """
    Redirect to login page
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Redirecting...</title>
        <script>
            window.location.href = '/login';
        </script>
    </head>
    <body>
        <p>Redirecting to login...</p>
    </body>
    </html>
    """


@app.route("/login", methods=["GET"])
def login_page():
    """
    Serve the login page
    """
    try:
        with open('login.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"message": "Login page not found"}), 404


@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    """
    Serve the dashboard page
    """
    try:
        with open('dashboard.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"message": "Dashboard page not found"}), 404


# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"message": "Internal server error"}), 500


# Run the app
if __name__ == "__main__":
    app.run(debug=False, port=5001)