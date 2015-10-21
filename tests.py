import server
import unittest
import json
from pymongo import MongoClient
import base64


def make_auth_header(username='admin', password='secret'):
    user_credentials = '{0}:{1}'.format(username, password)
    encoded_cred = base64.b64encode(user_credentials.encode('utf-8')).decode('utf-8')
    auth_header = {'Authorization': 'Basic ' + encoded_cred}
    return auth_header


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        # Run app in testing mode to retrieve exceptions and stack traces
        server.app.config['TESTING'] = True

        # Inject test database into application
        mongo = MongoClient('localhost', 27017)
        db = mongo.test_database
        server.app.db = db

        # Drop collection (significantly faster than dropping entire db)
        db.drop_collection('trips')

    def test_posting_user(self):
        head = make_auth_header()
        response = self.app.post('/users/',
                                 data=json.dumps(dict(password="secret")),
                                 content_type='application/json',
                                 headers=head)

        self.assertEqual(response.status_code, 200)

    def test_posting_trip(self):
        response = self.app.post('/trips/',
                                 data=json.dumps(dict(name="A sample trip")),
                                 content_type='application/json',
                                 headers=make_auth_header())

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'A sample trip' in responseJSON["name"]

    def test_getting_single_trip(self):
        response = self.app.post('/trips/',
                                 data=json.dumps(dict(name="Another trip")),
                                 content_type='application/json',
                                 headers=make_auth_header())

        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON["_id"]

        response = self.app.get('/trips/'+postedTripID, headers=make_auth_header())
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'Another trip' in responseJSON["name"]

    def test_getting_non_existent_trip(self):
        response = self.app.get('/trips/55f0cbb4236f44b7f0e3cb23', headers=make_auth_header())
        self.assertEqual(response.status_code, 404)

    def test_getting_all_trips(self):
        response = self.app.post('/trips/',
                                 data=json.dumps(dict(name="First trip", username="admin")),
                                 content_type='application/json',
                                 headers=make_auth_header())

        response = self.app.post('/trips/',
                                 data=json.dumps(dict(name="Another trip", username="admin")),
                                 content_type='application/json',
                                 headers=make_auth_header())

        response = self.app.get('/trips/', headers=make_auth_header())
        responseJSON = json.loads(response.data.decode())


        self.assertEqual(response.status_code, 200)
        assert 'First trip' in responseJSON[0]['name']
        assert 'Another trip' in responseJSON[1]['name']

    def test_updating_trip(self):
        response = self.app.post('/trips/',
                                 data=json.dumps(dict(name='another trip')),
                                 content_type='application/json',
                                 headers=make_auth_header())
        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON['_id']

        response = self.app.put('/trips/'+postedTripID,
                data=json.dumps(dict(name='spring break')),
                content_type='application/json',
                headers=make_auth_header())
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'spring break' in responseJSON['name']

    def test_deleting_trip(self):
        head = make_auth_header()
        response = self.app.post('/trips/',
                data=json.dumps(dict(name='delete this trip!')),
                content_type='application/json',
                headers=head)
        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON['_id']

        response = self.app.delete('/trips/'+postedTripID, headers=head)
        response = self.app.get('/trips/'+postedTripID, headers=head)
        self.assertEqual(response.status_code, 404)

    def test_auth(self):
        response = self.app.get('/users/',
                content_type='application/json',
                headers=make_auth_header())
        # postResponseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
