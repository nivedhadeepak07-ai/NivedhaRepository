from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os

# Creates the Flask application instance 
app = Flask(__name__)

# Allows CORS (cross-origin requests) to api 
# Required so that browser can call Flask APIs 
CORS(app, resources={r"/api/*": {"origins": "*"}})


#SECRET_KEY = used to sign and verify JWT tokens (has to match exactly)
#JWT_EXPIRATION_HOURS = how long tokens are valid for (in this scenario its 24 hrs)
SECRET_KEY = "your-secret-key-change-this-in-production"  
JWT_EXPIRATION_HOURS = 24

#Stimulates a real database by storing username, password, email, 
# enrollment date, status, courses, GPA 
# used only for testing/demo
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



# JWT Authentication Middleware = protects routes so only logged-in users can access them 
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allows CORS preflight (browser performs preflight checks so it prevents CORS errors)
        if request.method == "OPTIONS":
            return "", 204
        
        token = None

        #Extract JWT token = reads token from request header (returns 401 if the header is missing or token is not working)
        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Token format invalid"}), 401

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            # Decode JWT token = verifies signature, expiration, token integrity (extracts username)
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = data.get("username")

            if not username or username not in MOCK_USERS:
                return jsonify({"message": "User not found"}), 401

            # Checks if the username exists within MOCK_USERS 
            # Rejects request if its invalid 
            current_user = MOCK_USERS[username]

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        
        # Passes user info to the route = makes the data avaliable to the function
        return f(username, current_user, *args, **kwargs)

    return decorated

# ROUTES

@app.route("/api/login", methods=["POST"])
def login():
    """
    Login endpoint - Authenticates user and returns JWT token
    
    How it works: 
    1. Reads the request 
    2. Validates the username & password 
    3. Verifies that the info is within MOCK_USERS
    4. Creates JWT token with the username, issued at time, expiration time
    5. Signs the token with SECRET_KEY 
    6. Returns the token to the client 
    """
    data = request.get_json()
    
    # Validate & reads the request to make sure it contains username and password
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "Missing username or password"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    # Check if the credentials are within MOCK_USERS 
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"message": "Invalid credentials"}), 401

    
    # CREATES JWT TOKEN
    # Create the data stored in the token (known as payload)
    payload = {
        "username": username,
        "iat": datetime.utcnow(),  # Issued at time
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)  # Expiration time
    }
    
    # Encode token using SECRET_KEY
    # Uses HS256 algorithm - used to sign the token so that the server can verify that it was issued
    # by someone who knows the SECRET_KEY 
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        "token": token,
        "username": username,
        "message": "Login successful"
    }), 200

# Returns the full profile information
# Makes sure that the data is specific to the logged in user 
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

# Returns the detailed profile information from the mock data after the JWT token is verified 
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

#Logout Endpoint = requires a valid JWT & returns a logout message 
@app.route("/api/logout", methods=["POST"])
@token_required
def logout(username, current_user):
    """
    Logout endpoint
    
    Note: the client just deletes the token from localStorage 

    """
    return jsonify({
        "message": f"Goodbye, {username}!",
        "status": "logged_out"
    }), 200

# Public endpoint = no authentication required, accessible to anyone 
@app.route("/api/public", methods=["GET"])
def public():
    """
    Public endpoint - No authentication required
    """
    return jsonify({
        "message": "This is a public endpoint",
        "data": "Anyone can access this"
    }), 200

# Redirects the user to the login page 
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
# the info above is a simple HTML page that redirects the browser to /login 

# Acts as the login page 
# Returns 404 if the file is missing 
@app.route("/login", methods=["GET"])
def login_page():
    """
    Acts as the login page
    """
    try:
        with open('login.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"message": "Login page not found"}), 404

# Acts as the dashboard page 
# The frontend will handle the authentication 
@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    """
    Acts as the dashboard page
    """
    try:
        with open('dashboard.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({"message": "Dashboard page not found"}), 404


# Error handling 
# 404 - returns JSON error message for not found endpoints 
# 500 - catches unexpected server crashes 
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"message": "Internal server error"}), 500


# Starts the Flask server 
# Runs on port 5001 with debug mod off so that it induces production-safe behavior 
if __name__ == "__main__":
    app.run(debug=False, port=5001)