
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

db = SQLAlchemy()

##############################################################################
# Database Model Classes


class Region(db.Model):
    """Electric grid regions for the United States."""

    __tablename__ = 'regions'

    region_id = db.Column(db.String(9), primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    lb_CO2e_MWh = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return "<Region Id=%s, Region=%s, CO2e/MWH=%s>" % \
            (self.region_id, self.name, self.lb_CO2e_MWh)


class Zipcode(db.Model):
    """The grid region for every zipcode in the United States."""

    __tablename__ = 'zipcodes'

    zipcode_id = db.Column(db.String(16), primary_key=True)
    region_id = db.Column(db.String(9), db.ForeignKey('regions.region_id'),
                          nullable=False)

    def __repr__(self):
        return "<Zipcode=%s, Region Id=%s>" % \
            (self.zipcode_id, self.region_id)


class Car(db.Model):
    """Every car by make, model and year in the EPA fuel economy registry.
    Include CO2 and MPG data."""

    __tablename__ = 'cars'

    car_id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    fuel_type = db.Column(db.String(64), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    grams_CO2_mile = db.Column(db.Float, nullable=True)
    mpg_street = db.Column(db.Float, nullable=True)
    mpg_hw = db.Column(db.Float, nullable=True)
    mpg_combo = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return "<Car Id=%s, Make=%s, Model=%s, Year=%s>" % \
            (self.car_id, self.make, self.model, self.year)

    usercars = db.relationship('UserCar')


class User(db.Model):
    """User of carbon footprint calculator."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.Unicode(256), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.Unicode(256), nullable=False)

    def __repr__(self):
        return "<User Id=%s, Name=%s>" % (self.user_id, self.name)

    residences = db.relationship('Residence')


class UserCar(db.Model):
    """Car profiles for users. Users may have multiple cars."""

    __tablename__ = 'user_cars'

    user_car_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                        nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.car_id'), nullable=False)
    is_default = db.Column(db.Boolean, nullable=True)

    def __repr__(self):
        return "<User Car=%s, User Id=%s, Car Id=%s>" % \
            (self.user_car_id, self.user_id, self.car_id)

    car = db.relationship('Car')

    @classmethod
    def create(cls, user_id, make, model, year, is_default):

        current_cars = cls.query.filter_by(user_id=user_id).all()

        if is_default and current_cars:
            for car in current_cars:
                car.is_default = False

        car = Car.query.filter(Car.make == make, Car.model == model,
                               Car.year == year).first()

        new_car = cls(user_id=user_id, car=car, is_default=is_default)

        db.session.add(new_car)
        db.session.commit()


class TransitType(db.Model):
    """Mode of transportation with default carbon value for each."""

    __tablename__ = 'transit_type'

    transit_type_id = db.Column(db.Integer, autoincrement=True,
                                primary_key=True)
    transit_type = db.Column(db.Unicode(64), nullable=False)
    grams_CO2_mile = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<ID=%s, Transit Type=%s>" % (self.transit_type_id,
                                             self.transit_type)


class TripLog(db.Model):
    """Log of all user trips."""

    __tablename__ = 'trip_log'

    trip_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                        nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.car_id'), nullable=True)
    transportation_type = db.Column(db.Integer,
                                    db.ForeignKey('transit_type.transit_type_id'),
                                    nullable=False)
    date = db.Column(db.Date, nullable=False)
    miles = db.Column(db.Float, nullable=False)
    number_of_passengers = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<ID=%s, User=%s, Car=%s, Type=%s, Miles=%s, Date=%s>" % \
            (self.trip_id, self.user_id, self.car_id,
             self.transportation_type, self.miles, self.date)

    car = db.relationship('Car')

    @classmethod
    def create(cls, user_id, car_id, date, miles,
               number_of_passengers=1, transportation_type=1):

        new_trip = cls(user_id=user_id, car_id=car_id,
                       transportation_type=transportation_type, date=date,
                       miles=miles, number_of_passengers=number_of_passengers)

        db.session.add(new_trip)
        db.session.commit()

    def co2_calc(self):
        """Calculate the CO2 emissions for kwh entry."""

        co2 = 99999
        return co2


class Residence(db.Model):
    """Residence profiles for users. Users may have many residences."""

    __tablename__ = 'residences'

    residence_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                        nullable=False)
    zipcode_id = db.Column(db.String(16), db.ForeignKey('zipcodes.zipcode_id'),
                           nullable=False)
    name_or_address = db.Column(db.Unicode(256), nullable=False)
    is_default = db.Column(db.Boolean, nullable=True)
    number_of_residents = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<Residence Id=%s, user=%s, zipcode=%s>" % \
            (self.residence_id, self.user_id, self.zipcode_id)

    # relationships
    user = db.relationship('User')
    electricity_logs = db.relationship('ElectricityLog')
    ng_logs = db.relationship('NGLog')
    region = db.relationship("Region",
                             secondary="zipcodes",
                             backref="residences",
                             uselist=False)

    @classmethod
    def create(cls, user_id, zipcode_id, name_or_address, is_default,
               number_of_residents):

        current_residences = cls.query.filter_by(user_id=user_id).all()

        if is_default and current_residences:
            for residence in current_residences:
                residence.is_default = False

        new_residence = cls(user_id=user_id, zipcode_id=zipcode_id,
                            name_or_address=name_or_address,
                            is_default=is_default,
                            number_of_residents=number_of_residents)

        db.session.add(new_residence)
        db.session.commit()


class ElectricityLog(db.Model):
    """Log of user electricity usage."""

    __tablename__ = 'electricity_log'

    elect_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    residence_id = db.Column(db.Integer, db.ForeignKey('residences.residence_id'),
                             nullable=False)
    kwh = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return "<Id= %s, Residence= %s, kwh= %s, date= %s to %s>" % \
            (self.elect_id, self.residence_id, self.kwh, self.start_date,
             self.end_date)

    # Define relationship to residence
    residence = db.relationship('Residence')

    def kWh_to_MWh(self):
        """Convert kWh entered by users into MWh to match the EPA factor"""

        # 1 Kwh = 0.001 Megawatt Hours
        MWh = self.kwh * 0.001
        return MWh

    def co2_calc(self):
        """Calculate the CO2 emissions for kwh entry."""

        lb_CO2e_MWh = self.residence.region.lb_CO2e_MWh
        MWh = self.kWh_to_MWh()

        CO2e = MWh * lb_CO2e_MWh
        return CO2e


class NGLog(db.Model):
    """Log of user natural gas usage."""

    __tablename__ = 'ng_log'

    ng_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    residence_id = db.Column(db.Integer, db.ForeignKey('residences.residence_id'),
                             nullable=False)
    therms = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return "<Id= %s, Residence= %s, therms= %s, date= %s to %s>" % \
            (self.ng_id, self.residence_id, self.therms, self.start_date,
             self.end_date)

    # Define relationship to residence
    residence = db.relationship('Residence')

    def co2_calc(self):
        """Calculate the CO2 emissions for kwh entry."""

        tonnes_CO2_per_therm = 0.005302  # 0.005302 metric tons CO2/therm
        pounds_per_tonne = 2204.620  # 2,204.620 pounds per tonne

        CO2e = self.therms * tonnes_CO2_per_therm * pounds_per_tonne
        return CO2e

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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///carbon_calc'
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

    # db.create_all()
