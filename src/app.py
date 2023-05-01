import json
from db import db
from flask import Flask, request
from db import Course, Assignment, User
import os
import users_dao

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code

def extract_token(request):
    """
    Helper method for extracting token
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("missing authorization header")
    bearer_token = auth_header.replace("Bearer", "").strip()
    if not bearer_token:
        return False, failure_response("Invalid bearer token")
    return True, bearer_token
# your routes here

@app.route("/register/", methods=["POST"])
def register():
    """
    Endpoint for registering a user
    """
    body = json.loads(request.data)
    name = body.get("name")
    bio = body.get("bio")
    email = body.get("email")
    password = body.get("password")

    if name is None or bio is None or email is None or password is None:
        return failure_response("Invalid response to required fields")
    
    created, user = users_dao.create_user(email, password, name, bio)
    if not created:
        return failure_response("This user already exists.")
    
    return success_response({"session_token": user.session_token, "session_expiration": str(user.session_expiration), "update_token": user.update_token})

@app.route("/login/", methods=["POST"])
def login():
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Invalid username or password.")
    
    success, user = users_dao.verify_credentials(email, password)
    if not success:
        return failure_response("Invalid username or password.")
    
    return success_response({"session_token": user.session_token, "session_expiration": str(user.session_expiration), "update_token": user.update_token})

@app.route("/secret/", methods=["POST"])
def secret_message():
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is not None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token")
    return success_response({"message": "Session tokens are working."})

@app.route("/session/", methods=["Post"])
def update_session():
    """
    Endpoint for updating a users session.
    """
    success, update_token = extract_token(request)
    if not success:
        return update_token
    user = users_dao.renew_session(update_token)

    if user is None:
        return failure_response("Invalid update token")
    
    return success_response({"session_token": user.session_token, "session_expiration": str(user.session_expiration), "update_token": user.update_token})
    




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
