# model.py
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

mongo = PyMongo()
users_col = None

def init_app(app):
    global users_col
    mongo.init_app(app)
    users_col = mongo.db.users

def user_exists(username):
    return users_col.find_one({'username': username})

def create_user(user_data):
    user_data['password'] = generate_password_hash(user_data['password'])
    return users_col.insert_one(user_data)

def validate_user(role, username, password):
    user = users_col.find_one({'username': username, 'role': role})
    if user and check_password_hash(user['password'], password):
        return user
    return None

def get_all_users():
    return list(users_col.find({}, {'password': 0}))
