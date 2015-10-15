import server
import unittest
import json
from pymongo import MongoClient


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
        db.drop_collection('myobjects')

    # MyObject tests

    def test_posting_trip(self):
        response = self.app.post('/trip/',
                                 data=json.dumps(dict(name="A sample trip")),
                                 content_type='application/json')

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'A sample trip' in responseJSON["name"]

    def test_getting_trip(self):
        response = self.app.post('/trip/',
                                 data=json.dumps(dict(name="Another trip")),
                                 content_type='application/json')

        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON["_id"]

        response = self.app.get('/trip/'+postedTripID)
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'Another trip' in responseJSON["name"]

    def test_getting_non_existent_trip(self):
        response = self.app.get('/trip/55f0cbb4236f44b7f0e3cb23')
        self.assertEqual(response.status_code, 404)

    def test_updating_trip(self):
        response = self.app.post('/trip/', data=json.dumps(dict(name='another trip')), content_type='application/json')
        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON['_id']

        response = self.app.put('/trip/'+postedTripID, data=json.dumps(dict(name='spring break')))
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'spring break' in responseJSON['name']

    def test_deleting_trip(self):
        response = self.app.post('/trip/', data=json.dumps(dict(name='delete this trip!')), content_type='application/json')
        postResponseJSON = json.loads(response.data.decode())
        postedTripID = postResponseJSON['_id']

        response = self.app.delete('/trip/'+postedTripID)
        response = self.app.get('/trip/'+postedTripID)
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
