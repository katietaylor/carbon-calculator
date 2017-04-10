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


class NoLoginIntegrationTest(TestCase):
    """Test each route when there is no user logged in."""

    def setUp(self):
        tc = app.test_client()
        self.client = tc

    def test_login_page(self):
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn("Login", resp.data)

    def test_profile_page(self):
        resp = self.client.get("/profile")
        self.assertEqual(302, resp.status_code)

    def test_carbonlog_page(self):
        resp = self.client.get("/carbon-log")
        self.assertEqual(302, resp.status_code)

    def test_kwhlog_page(self):
        resp = self.client.get("/kwh-log")
        self.assertEqual(302, resp.status_code)

    def test_nglog_page(self):
        resp = self.client.get("/ng-log")
        self.assertEqual(302, resp.status_code)

    def test_triplog_page(self):
        resp = self.client.get("/trip-log")
        self.assertEqual(302, resp.status_code)


class BasicIntegrationTest(TestCase):
    """Integration tests to make sure each route is loading with the test data
    displayed as expected."""

    def setUp(self):
        tc = app.test_client()
        self.client = tc
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'ABC'
        connect_to_db(app, "postgresql:///test_carbon_calc")

        # Create tables and add sample data
        db.create_all()
        initialize_test_data()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

    def tearDown(self):
        """Do at end of every test."""

        db.session.close()
        db.drop_all()

    def test_login_page(self):
        resp = self.client.get("/")
        self.assertEqual(200, resp.status_code)
        self.assertIn("Logout", resp.data)

    def test_profile_page(self):
        resp = self.client.get("/profile")
        self.assertEqual(200, resp.status_code)
        self.assertIn("Home", resp.data)
        self.assertIn("Beach House", resp.data)
        self.assertIn("Prius", resp.data)
        self.assertIn("4Runner", resp.data)

    def test_carbonlog_page_kwh(self):
        resp = self.client.get("/carbon-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("188", resp.data)
        self.assertIn("Home", resp.data)
        self.assertIn("116.9", resp.data)

    def test_carbonlog_page_ng(self):
        resp = self.client.get("/carbon-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("30", resp.data)
        self.assertIn("350.6", resp.data)

    def test_carbonlog_page_trip(self):
        resp = self.client.get("/carbon-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("100", resp.data)
        self.assertIn("Prius", resp.data)
        self.assertIn("42.5", resp.data)

    def test_kwhlog_page(self):
        resp = self.client.get("/kwh-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("188", resp.data)
        self.assertIn("Home", resp.data)
        self.assertIn("116.9", resp.data)

    def test_nglog_page(self):
        resp = self.client.get("/ng-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("30", resp.data)
        self.assertIn("350.6", resp.data)

    def test_triplog_page(self):
        resp = self.client.get("/trip-log")
        self.assertEqual(200, resp.status_code)
        self.assertIn("100", resp.data)
        self.assertIn("Prius", resp.data)
        self.assertIn("42.5", resp.data)

    def test_cardata_page(self):
        resp = self.client.get("/car-data")
        self.assertEqual(200, resp.status_code)
        self.assertIn("{", resp.data)
        self.assertIn("cylinders", resp.data)
        self.assertIn("model", resp.data)


class AddToProfile(TestCase):
    """Integration tests to make sure each route is loading with the test data
    displayed as expected."""

    def setUp(self):
        tc = app.test_client()
        self.client = tc
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'ABC'
        connect_to_db(app, "postgresql:///test_carbon_calc")

        # Create tables and add sample data
        db.create_all()
        initialize_test_data()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

    def tearDown(self):
        """Do at end of every test."""

        db.session.close()
        db.drop_all()

    def add_residence(self, name, zipcode, number_of_residents, is_default):
        return self.app.post('/add-residence', data=dict(
            name_or_address=name,
            zipcode=zipcode,
            number_of_residents=number_of_residents,
            is_default=is_default
            ), follow_redirects=True)

    def test_adding_residence(self):
        rv = self.add_residence("Treehouse", 94133, 2, True)
        self.assertIn("Treehouse", rv.data)


# /add-car
# /add-kwh
# /add-ng
# /add-residence
# /add-trip
# /edit-kwh
# /edit-ng
# /edit-residence
# /edit-trip
# /get-distance
# /logout
# /process-login
# /process-signup

if __name__ == "__main__":
    import unittest

    unittest.main()
