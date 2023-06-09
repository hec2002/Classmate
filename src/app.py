import json
from db import db, User, Friendship, Schedule, Class
from flask import Flask, request
import os
import users_dao
import datetime

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


@app.route('/api/users/')
def get_all_users():
    """
    Route that gets all users.
    """
    users = [user.serialize() for user in User.query.all()]
    return success_response({"user": users})

@app.route('/api/classes/')
def get_all_classes():
    """
    Route that gets all users.
    """
    classes = [clas.serialize() for clas in Class.query.all()]
    return success_response({"Classes": classes})

@app.route('api/schedules/')
def get_all_schedules():
    """
    Route that gets all users.
    """
    schedules = [schedule.serialize() for schedule in Schedule.query.all()]
    return success_response({"Schedules": schedules})

@app.route('/api/friends/')
def get_all_friendships():
    """
    Route that gets all users.
    """
    friendships = [friendship.serialize() for friendship in Friendship.query.all()]
    return success_response({"Friendships": friendships})


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


@app.route("/api/register/", methods=["POST"])
def register():
    """
    Endpoint for registering a user
    """
    body = json.loads(request.data)
    name = body.get("name")
    netid = body.get("netid")
    email = body.get("email")
    password = body.get("password")

    if name is None or netid is None or email is None or password is None:
        return failure_response("Invalid response to required fields")

    created, user = users_dao.create_user(email, password, name, netid)
    schedule = Schedule(user_id=user.id)
    db.session.add(schedule)
    db.session.add(user)
    db.session.commit()

    if not created:
        return failure_response("This user already exists.")

    return success_response({"session_token": user.session_token, "session_expiration": str(user.session_expiration), "update_token": user.update_token})


@app.route("/api/login/", methods=["POST"])
def login():
    """
    Endpoint for logging a user in
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Invalid username or password.")

    success, user = users_dao.verify_credentials(email, password)
    if not success:
        return failure_response("Invalid username or password.")

    return success_response({"session_token": user.session_token, "session_expiration": str(user.session_expiration), "update_token": user.update_token})


@app.route("/api/secret/", methods=["POST"])
def secret_message():
    """
    Endpoint for secret message (Testing only)
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token")
    return success_response({"message": "Session tokens are working."})


@app.route("/api/session/", methods=["POST"])
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


@app.route("/api/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging a user out.
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token.")
    user.session_expiration = datetime.datetime.now()
    db.session.commit()
    return success_response({"message": "logout successful"})

# new routes added for app functionality 


@app.route('/api/users/<int:id>/', methods=['GET'])
def get_user(id):
    """
    Endpoint for getting a user by id.
    """
    user = User.query.filter_by(id=id).first()
    if user is None:
        return failure_response("Invalid user id.")
    return success_response(user.serialize())


@app.route('/api/classes/<int:id>/', methods=['DELETE'])
def delete_class(id):
    """
    Endpoint for deleting a class.
    """
    class_to_delete = Class.query.get_or_404(id)
    db.session.delete(class_to_delete)
    db.session.commit()
    return success_response({'message': 'Class deleted successfully!'})



@app.route('/api/classes/<int:id>/', methods=['POST'])
def add_class(id):
    """
    Endpoint for adding a class.
    """
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        return failure_response("Invalid schedule id.")
    body = json.loads(request.data)
    name = body.get("name")
    code = body.get("code")
    typ = body.get("type")
    start_hour = body.get("start_hour")
    start_minute = body.get("start_minute")
    start_period = body.get("start_period")
    end_hour = body.get("end_hour")
    end_minute = body.get("end_minute")
    end_period = body.get("end_period")
    days = body.get("days")
    if name is None or code is None or typ is None or start_hour is None or start_minute is None or start_period is None or end_hour is None or end_minute is None or end_period is None or days is None:
        return failure_response("One of your inputs is invalid.")
    new_class = Class(start_hour=start_hour, start_minute=start_minute, start_period=start_period, code=code, name=name, type=typ, end_hour=end_hour, end_minute=end_minute, end_period=end_period, days=days)
    new_class.schedule = id
    db.session.add(new_class)
    db.session.commit()
    return success_response(new_class.serialize())

@app.route('/api/users/<int:sender_id>/request/', methods=['POST'])
def send_friend_request(sender_id):
    """
    Endpoint for sending a friend request
    """
    sender = User.query.filter_by(id=sender_id).first()
    if sender is None:
        return failure_response("Invalid sender id.")
    body = json.loads(request.data)
    netid = body.get("netid")
    user = User.query.filter_by(netid=netid).first()
    if user is None:
        return failure_response("User not found.")
    new_request = Friendship(sender_id=sender_id, receiver_id=user.id, accepted=0, timestamp=datetime.datetime.now())
    db.session.add(new_request)
    db.session.commit()
    return success_response(new_request.serialize())


@app.route('/api/friends/requests/<int:request_id>/', methods=['POST'])
def add_friend(request_id):
    """
    Endpoint for adding a friend to a user.
    """
    friend_request = Friendship.query.filter_by(id=request_id).first()
    if friend_request is None:
        return failure_response("Friend request not found.")
    if friend_request.accepted != 0:
        return failure_response("Request has already been responded to.")
    body = json.loads(request.data)
    accepted = body.get("accepted")
    if accepted == "declined":
        db.session.delete(friend_request)
        db.session.commit()
        return success_response({"status": "Request Denied."})
    elif accepted == "accepted":
        friend_request.accepted = 1
        db.session.commit()
        return success_response(friend_request.serialize())
    else:
        return failure_response("Invalid response")

@app.route('/api/students/<int:user_id>/schedules/', methods=['POST'])
def recommend(user_id):
    """
    Endpoint for generating class recommendations based on friends.
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("Invalid user.")
    friends = Friendship.query.filter((Friendship.sender_id == user_id) | (Friendship.reciever_id == user_id), Friendship.accepted == 1)
    if not friends:
        return failure_response("No friends to add.")
    friends_as_list = [friend.serialize() for friend in friends]
    dic = {}
    for friend in friends_as_list:
        if friend["sender_id"] == user_id:
            dic[friend["receiver_id"]] = 0
        else:
            dic[friend["sender_id"]] = 0
    for id in dic:
        schedule = Schedule.query.filter_by(user_id=id).first()
        classes = [clas.simple_serialize() for clas in schedule.classes]
        dic[id] = classes
    classes_in_common = {}
    for user1 in dic:
        for user2 in dic:
            if user1 == user2 or str(user2) + " " + str(user1) in dic:
                continue
            else:
                common = [clas for clas in dic[user1] if clas in dic[user2]]
                classes_in_common[str(user1) + " " + str(user2)] = common
    return success_response(classes_in_common)



@app.route('/api/schedules/<int:id>/', methods=['GET'])
def get_schedule(id):
    """
    Endpoint for getting a schedule.
    """
    schedule = Schedule.query.get_or_404(id)
    classes = Class.query.filter_by(schedule=id).all()
    serialized_classes = [c.serialize() for c in classes]
    return json.dumps({
        'id': schedule.id,
        'user_id': schedule.user_id,
        'classes': serialized_classes
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
