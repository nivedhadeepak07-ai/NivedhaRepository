# Student Portal – JWT Authentication Web Application

A full-stack student portal demonstration built using Python, Flask, HTML, CSS, JavaScript, and JSON Web Tokens (JWT).

### Features
- User authentication using JWT
- Personalized student dashboard
- Protected REST API endpoints
- Student profile displaying courses, GPA, and enrollment information
- Token verification and expiration handling
- Responsive interface built with HTML and CSS
- Client-side logout functionality

### Technologies Used
- **Backend:** Python, Flask, Flask-CORS
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** JWT (HS256)
- **API:** RESTful endpoints

### How to Run
1. Install dependencies: `pip install flask flask-cors PyJWT`
2. Set the `SECRET_KEY` environment variable to a development secret.
3. Run `python app.py`.
4. Open `http://127.0.0.1:5001/login`.

### Purpose
This project was developed to explore web authentication, REST API integration, and frontend-backend communication. It demonstrates how protected routes and user-specific dashboards can be implemented in a web application.

**Note:** This is an educational demonstration using mock student data, not a production authentication system.
