
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

##############################################################################
# Database Model Classes


class User(db.Model):
    """User of carbon diary."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.Unicode(256), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.Unicode(256), nullable=False)
    username = db.Column(db.Unicode(256), nullable=False)


class Region(db.Model):

    __tablename__ = 'regions'

    region_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Unicode(256), nullable=False)
    lb_CO2e_kwh = db.Column(db.Integer, nullable=False)


class Zipcode(db.Model):

    __tablename__ = 'zipcodes'

    zipcode_id = db.Column(db.String(16), primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('Region.region_id'), nullable=False)


class Car(db.Model):
    __tablename__ = 'cars'

    car_id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.Unicode(100), nullable=False)
    model = db.Column(db.Unicode(100), nullable=False)
    fuel_type = db.Column(db.Unicode(100), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    grams_CO2_mile = db.Column(db.Integer, nullable=True)
    mpg_street = db.Column(db.Integer, nullable=True)
    mpg_hw = db.Column(db.Integer, nullable=True)
    mpg_combo = db.Column(db.Integer, nullable=True)


class User_Car(db.Model):

    __tablename__ = 'user_cars'

    user_car_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('Car.car_id'), nullable=False)
    is_default = db.Column(db.Boolean, nullable=True)


class Residences(db.Model):

    __tablename__ = 'residences'

    residence_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    zipcode_id = db.Column(db.Integer, db.ForeignKey('Zipcode.zipcode_id'), nullable=False)
    address = db.Column(db.Unicode(256), nullable=False)
    is_default = db.Column(db.Boolean, nullable=True)


class Transit_Log(db.Model):
    __tablename__ = 'transit_log'


class Transportation_Type(db.Model):
    __tablename__ = 'transportation_type'
    

class Electricity_Log(db.Model):
    __tablename__ = 'electricity_log'
   

class NG_Log(db.Model):
    __tablename__ = 'ng_log'

##############################################################################
# Helper functions

def init_app():
    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our database.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///cars'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask

    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."
