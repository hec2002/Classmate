"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

import db


def get_user_by_email(email):
    """
    Returns a user object from the database given an email
    """
    return db.User.query.filter(db.User.email == email).first()


def get_user_by_session_token(session_token):
    """
    Returns a user object from the database given a session token
    """
    return db.User.query.filter(db.User.session_token == session_token).first()


def get_user_by_update_token(update_token):
    """
    Returns a user object from the database given an update token
    """
    return db.User.query.filter(db.User.update_token == update_token).first()


def verify_credentials(email, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    user = get_user_by_email(email)
    if user is None:
        return False, None
    
    return user.verifypassword(password), user 
    
def create_user(email, password, name, netid):
    """
    Creates a User object in the database

    Returns if creation was successful, and the User object
    """
    optional_user = get_user_by_email(email)
    if optional_user is not None:
        return False, optional_user
    
    user = db.User(name=name, email=email, password=password, netid=netid)
    db.session.add(user)
    db.session.commit()

    return True, user

def renew_session(update_token):
    """
    Renews a user's session token
    
    Returns the User object
    """
    user = get_user_by_update_token(update_token)
    if user is None:
        return None
    user.renew_session()
    db.session.commit()
    return user
