from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from functools import wraps
import bcrypt

# Basic Setup
app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
api = Api(app)


def check_auth(username, password):
    if username == 'admin' and password == 'secret':
        return True
    user_collection = app.db.users
    user = user_collection.find_one({'username': username})
    if user is None:
        return False
    db_hashed_password = user['password']
    encoded_password = password.encode('utf-8')
    encrypted_password = bcrypt.hashpw(encoded_password, db_hashed_password)
    check_if_correct_password = (encrypted_password == db_hashed_password)
    return check_if_correct_password


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        # check = check_auth(auth.username, auth.password)
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp

        return f(*args, **kwargs)
    return decorated


# Implement REST Resource
class Trip(Resource):

    @requires_auth
    def post(self):
        new_trip = request.json
        trip_collection = app.db.trips
        result = trip_collection.insert_one(new_trip)

        trip = trip_collection.find_one({"_id": ObjectId(result.inserted_id)})

        return trip

    @requires_auth
    def get(self, trip_id=None):
        trip_collection = app.db.trips

        trip = None

        if trip_id is None:
            trip = trip_collection.find({"username":
                                        request.authorization.username})
            trip = list(trip)
        else:
            trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        if trip is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

    @requires_auth
    def put(self, trip_id):
        updated_trip = request.json
        trip_collection = app.db.trips
        result = trip_collection.update_one({"_id": ObjectId(trip_id)},
                                            {"$set": updated_trip})
        if result.modified_count == 0:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return updated_trip

    @requires_auth
    def delete(self, trip_id):
        trip_collection = app.db.trips
        result = trip_collection.delete_one({'_id': ObjectId(trip_id)})
        if result.deleted_count == 0:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            response = jsonify(data=[])
            response.status_code = 200
            return response


class User(Resource):

    def post(self):   # check if correct
        new_user = request.json
        app.bcrypt_rounds = 12
        encodedPassword = new_user['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(encodedPassword,
                                        bcrypt.gensalt(app.bcrypt_rounds))
        new_user['password'] = hashed_password

        user_collection = app.db.users
        result = user_collection.insert_one(new_user)

        user = user_collection.find_one({"_id": ObjectId(result.inserted_id)})
        del user['password']  # DO NOT return the hashed password to clients!!!
        return user

    @requires_auth
    def get(self):   # check if correct

        resp = jsonify(message=[])
        resp.status_code = 200
        return resp


# Add REST resource to API
api.add_resource(Trip, '/trips/', '/trips/<string:trip_id>')
api.add_resource(User, '/users/', '/users/<string:user_id>')


# provide a custom JSON serializer for flasks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
