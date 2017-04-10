
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
    lb_co2e_mega_wh = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return "<Region Id=%s, Region=%s, CO2e/MWH=%s>" % \
            (self.region_id, self.name, self.lb_co2e_mega_wh)


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
    cylinders = db.Column(db.String(64), nullable=True)
    drive = db.Column(db.String(64), nullable=True)
    eng_id = db.Column(db.String(64), nullable=True)
    eng_description = db.Column(db.String(64), nullable=True)
    displacement = db.Column(db.String(64), nullable=True)
    trans_description = db.Column(db.String(64), nullable=True)
    transmission = db.Column(db.String(64), nullable=True)
    grams_co2_mile = db.Column(db.Float, nullable=True)
    mpg_street = db.Column(db.Float, nullable=True)
    mpg_hw = db.Column(db.Float, nullable=True)
    mpg_combo = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return "<Car Id=%s, Make=%s, Model=%s, Year=%s>" % \
            (self.car_id, self.make, self.model, self.year)

    @classmethod
    def get_unique_makes(cls):
        """Get list of unique car makes (brands)."""

        query = db.session.query(cls.make).distinct()
        makes = sorted([row.make for row in query.all()])

        return makes

    def as_dict(self):
        """This method changes the results of a query into a dictionary. The
        column name is set to the dictionary key"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


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

    __tablename__ = 'usercars'

    usercar_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                        nullable=False)
    make = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    cylinders = db.Column(db.String(64), nullable=True)
    transmission = db.Column(db.String(64), nullable=True)
    is_default = db.Column(db.Boolean, nullable=True)

    def __repr__(self):
        return "<User Car=%s, User Id=%s, Car Id=%s>" % \
            (self.usercar_id, self.user_id, self.car_id)

    @classmethod
    def create(cls, user_id, make, model, year, cylinders, transmission,
               is_default):

        current_cars = cls.query.filter_by(user_id=user_id).all()

        if is_default and current_cars:
            for car in current_cars:
                car.is_default = False

        new_car = cls(user_id=user_id, make=make, model=model, year=year,
                      cylinders=cylinders, transmission=transmission,
                      is_default=is_default)

        db.session.add(new_car)
        db.session.commit()


class TransitType(db.Model):
    """Mode of transportation with default carbon value for each."""

    __tablename__ = 'transit_type'

    transit_type_id = db.Column(db.Integer, autoincrement=True,
                                primary_key=True)
    transit_type = db.Column(db.String(64), nullable=False)
    grams_co2_mile = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<ID=%s, Transit Type=%s>" % (self.transit_type_id,
                                             self.transit_type)


class TripLog(db.Model):
    """Log of all user trips."""

    __tablename__ = 'trip_log'

    trip_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),
                        nullable=False)
    usercar_id = db.Column(db.Integer, db.ForeignKey('usercars.usercar_id'),
                           nullable=True)
    transportation_type = db.Column(db.Integer,
                                    db.ForeignKey('transit_type.transit_type_id'),
                                    nullable=False)
    date = db.Column(db.Date, nullable=False)
    miles = db.Column(db.Float, nullable=False)
    number_of_passengers = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<ID=%s, User=%s, Car=%s, Type=%s, Miles=%s, Date=%s>" % \
            (self.trip_id, self.user_id, self.usercar_id,
             self.transportation_type, self.miles, self.date)

    usercar = db.relationship('UserCar')

    @classmethod
    def create(cls, user_id, usercar_id, date, miles,
               number_of_passengers=1, transportation_type=1):

        new_trip = cls(user_id=user_id, usercar_id=usercar_id,
                       transportation_type=transportation_type, date=date,
                       miles=miles, number_of_passengers=number_of_passengers)

        db.session.add(new_trip)
        db.session.commit()

    def co2_calc(self):
        """Calculate the CO2 emissions for a car trip."""

        grams_to_lbs = 0.00220  # 0.00220 pounds in a gram

        make = self.usercar.make
        model = self.usercar.model
        year = self.usercar.year
        cylinders = self.usercar.cylinders
        transmission = self.usercar.transmission

        # get all CO2 factors that meet the car search criteria
        grams_co2_mile = db.session.query(Car.grams_co2_mile).filter_by(
            make=make, model=model, year=year)

        if cylinders:
            grams_co2_mile = grams_co2_mile.filter_by(cylinders=cylinders)
        if transmission:
            grams_co2_mile = grams_co2_mile.filter_by(transmission=transmission)

        # convert list of tuples just a list of values
        grams_co2_mile = [factor[0] for factor in grams_co2_mile.all()]

        avg_grams_co2_mile = sum(grams_co2_mile) / len(grams_co2_mile)

        co2 = self.miles * avg_grams_co2_mile * grams_to_lbs
        return co2

    @classmethod
    def sum_trip_co2(cls, user_id, start_date="1/1/1900", end_date="1/1/2036"):
        """Sum the CO2 emissions from all of the trips within a given date
        range"""

        # trips = SELECT *
        #         FROM trip_log
        #         WHERE date >= start_date AND date <= end_date;

        trips = cls.query.filter(cls.user_id == user_id,
                                 cls.date >= start_date,
                                 cls.date <= end_date).all()

        total_co2 = 0
        for trip in trips:
            total_co2 += cls.co2_calc(trip)

        return total_co2


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

    def kwh_to_mega_wh(self):
        """Convert kWh entered by users into MWh to match the EPA factor"""

        # 1 Kwh = 0.001 Megawatt Hours
        mega_wh = self.kwh * 0.001
        return mega_wh

    def co2_calc(self):
        """Calculate the CO2 emissions for kwh entry."""

        lb_co2e_mega_wh = self.residence.region.lb_co2e_mega_wh
        mega_wh = self.kwh_to_mega_wh()

        co2e = mega_wh * lb_co2e_mega_wh
        return co2e

    @classmethod
    def sum_kwh_co2(cls, user_id, start_date="1/1/1900", end_date="1/1/2036"):
        """Sum the CO2 emissions from all of the kwhs within a given date
        range"""

    #     kwhs = SELECT *
    #            FROM electricity_log AS e
    #            JOIN residences AS r ON (e.residence_id=r.residence_id)
    #            WHERE r.user_id = user_id AND
    #                  (start_date BETWEEN cls.start_date AND cls.end_date OR
    #                   end_date BETWEEN cls.start_date AND cls.end_date OR
    #                   cls.start_date BETWEEN start_date AND end_date OR
    #                   cls.end_date BETWEEN start_date AND end_date)

        kwhs = cls.query.filter(cls.residence.has(Residence.user_id == user_id),
                                cls.start_date >= start_date,
                                cls.start_date <= end_date).all()

        total_co2 = 0
        for kwh in kwhs:
            total_co2 += cls.co2_calc(kwh)

        return total_co2


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

        tonnes_co2_per_therm = 0.005302  # 0.005302 metric tons CO2/therm
        pounds_per_tonne = 2204.620  # 2,204.620 pounds per tonne

        co2e = self.therms * tonnes_co2_per_therm * pounds_per_tonne
        return co2e

    @classmethod
    def sum_ng_co2(cls, user_id, start_date="1/1/1900", end_date="1/1/2036"):
        """Sum the CO2 emissions from all of the kwhs within a given date
        range"""

        ngs = cls.query.filter(cls.residence.has(Residence.user_id == user_id),
                               cls.start_date >= start_date,
                               cls.start_date <= end_date).all()

        total_co2 = 0
        for ng in ngs:
            total_co2 += cls.co2_calc(ng)

        return total_co2

##############################################################################
# Helper functions


def initialize_test_data():
    """Seed test database with test data."""

    # Region.query.delete()
    # Zipcode.query.delete()
    # Car.query.delete()
    # TransitType.query.delete()
    # User.query.delete()
    # UserCar.query.delete()
    # TripLog.query.delete()
    # ElectricityLog.query.delete()
    # NGLog.query.delete()
    # Residence.query.delete()

    region = Region(region_id="CAMX", name="WECC California",
                    lb_co2e_mega_wh=621.9)

    usa_region = Region(region_id="USA", name="United States",
                        lb_co2e_mega_wh=1150.3)

    zipcode = Zipcode(zipcode_id=94133, region_id="CAMX")

    car_one_type = Car(car_id=1, make="Toyota", model="Prius",
                       fuel_type="Regular Gasoline", year=2004,
                       cylinders=4, drive="Front-Wheel Drive", eng_id=0,
                       eng_description="", displacement=1.5,
                       trans_description="",
                       transmission="Automatic (variable gear ratios)",
                       grams_co2_mile=193.195652173913, mpg_street=48,
                       mpg_hw=45, mpg_combo=46)
    car_4runner_1 = Car(car_id=2, make="Toyota", model="4Runner 2WD",
                        fuel_type="Regular Gasoline", year=2004,
                        cylinders=6, drive="Rear-Wheel Drive", eng_id=0,
                        eng_description="", displacement=4.0,
                        trans_description="CLKUP",
                        transmission="Automatic 4-spd",
                        grams_co2_mile=493.722222222222, mpg_street=16,
                        mpg_hw=20, mpg_combo=18)
    car_4runner_2 = Car(car_id=3, make="Toyota", model="4Runner 2WD",
                        fuel_type="Regular Gasoline", year=2004,
                        cylinders=8, drive="Rear-Wheel Drive", eng_id=0,
                        eng_description="", displacement=4.7,
                        trans_description="CLKUP",
                        transmission="Automatic 5-spd",
                        grams_co2_mile=555.4375, mpg_street=15,
                        mpg_hw=18, mpg_combo=16)
    car_4runner_3 = Car(car_id=4, make="Toyota", model="4Runner 4WD",
                        fuel_type="Regular Gasoline", year=2004,
                        cylinders=6, drive="4-Wheel or All-Wheel Drive",
                        eng_id=0, eng_description="", displacement=4.0,
                        trans_description="CLKUP",
                        transmission="Automatic 4-spd",
                        grams_co2_mile=522.764705882353, mpg_street=15,
                        mpg_hw=19, mpg_combo=17)
    car_4runner_4 = Car(car_id=5, make="Toyota", model="4Runner 4WD",
                        fuel_type="Regular Gasoline", year=2004,
                        cylinders=8, drive="4-Wheel or All-Wheel Drive", eng_id=0,
                        eng_description="", displacement=4.7,
                        trans_description="CLKUP",
                        transmission="Automatic 5-spd",
                        grams_co2_mile=592.466666666667, mpg_street=14,
                        mpg_hw=17, mpg_combo=15)

    transit_type = TransitType(transit_type='car')

    user = User(user_id=1, email=u"cat@email.com", password="password", name=u"Phillipe")

    residence_1 = Residence(user_id=1, zipcode_id=94133, name_or_address=u"Home",
                            is_default=True, number_of_residents=1)
    residence_2 = Residence(user_id=1, zipcode_id=94133,
                            name_or_address=u"Beach House",
                            is_default=False, number_of_residents=2)

    usercar_1 = UserCar(user_id=1, make="Toyota", model="Prius", year=2004,
                        cylinders=4,
                        transmission="Automatic (variable gear ratios)",
                        is_default=True)
    usercar_2 = UserCar(user_id=1, make="Toyota", model="4Runner 4WD",
                        year=2004, cylinders=6, transmission="Automatic 4-spd",
                        is_default=False)

    triplog_1 = TripLog(user_id=1, usercar_id=1, transportation_type=1,
                        date="2017-01-01", miles=100, number_of_passengers=1)
    triplog_2 = TripLog(user_id=1, usercar_id=2, transportation_type=1,
                        date="2017-02-01", miles=310, number_of_passengers=2)
    elect_log_1 = ElectricityLog(start_date="2017-01-01", end_date="2017-02-01",
                                 kwh=188, residence_id=1)
    elect_log_2 = ElectricityLog(start_date="2017-01-15", end_date="2017-02-15",
                                 kwh=60, residence_id=2)

    ng_log = NGLog(start_date="2017-01-01", end_date="2017-02-01", therms=30,
                   residence_id=1)

    db.session.add_all([user, car_one_type, car_4runner_1, car_4runner_2,
                        car_4runner_3, car_4runner_4, usa_region, region,
                        transit_type])
    db.session.commit()

    db.session.add_all([zipcode])
    db.session.commit()

    db.session.add_all([residence_1, residence_2, usercar_1, usercar_2])
    db.session.commit()

    db.session.add_all([triplog_1, triplog_2, elect_log_1, elect_log_2, ng_log])
    db.session.commit()


def init_app():
    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."


def connect_to_db(app, uri='postgres:///carbon_calc'):
    """Connect the database to our Flask app."""

    # Configure to use our database.
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
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

    import doctest

    print
    result = doctest.testmod()
    if not result.failed:
        print "ALL TESTS PASSED. GOOD WORK!"
    print
