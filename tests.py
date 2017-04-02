from unittest import TestCase
from model import *
from server import app
from flask import session


class FlaskTestsDatabase(TestCase):
    def setUp(self):
        """Stuff to do before every test."""

        self.client = app.test_client()
        app.config['TESTING'] = True

        connect_to_db(app, "postgresql:///test_carbon_calc")

        # Create tables and add sample data
        db.create_all()
        initialize_test_data()

    def tearDown(self):
        """Do at end of every test."""

        db.session.close()
        db.drop_all()

    def test_trip_co2(self):

        car = Car.query.filter_by(car_id=1).one()
        self.assertIsNotNone(car)


# class ServerTests(TestCase):
#     """Tests for server."""

#     def setUp(self):
#         app.config['TESTING'] = True
#         self.client = app.test_client()

#     def test_homepage(self):
#         result = self.client.get("/")
#         self.assertIn("Sign Up", result.data)

if __name__ == "__main__":
    import unittest

    unittest.main()
