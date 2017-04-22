"""Carbon Calculator App"""

from datetime import datetime, date, timedelta
from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash,
                   session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension
from model import (connect_to_db, db, User, Residence, ElectricityLog, NGLog,
                   UserCar, Car, TripLog)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
import requests
import os

# source misc/secrets.sh in terminal before running server

app = Flask(__name__)

app.secret_key = "ABC"  # Required to use Flask sessions and the debug toolbar
app.jinja_env.undefined = StrictUndefined  # Undefined variable in Jinja2 will raise an error.

###  Users, Login, Signup, Logout #############################################


@app.route("/", methods=["GET"])
def homepage():
    """Renders login template if the user is not signed in and the homepage if
    the user is logged in."""

    user_id = session.get("user_id")

    if user_id:
        years = set()
        years.update(TripLog.get_trip_years(user_id),
                     ElectricityLog.get_kwh_years(user_id),
                     NGLog.get_ng_years(user_id)
                     )
        this_year = date.today().year

        makes = Car.get_unique_makes()
        usercars = UserCar.query.filter_by(user_id=user_id).order_by(
            UserCar.is_default.desc(), UserCar.usercar_id.desc()).all()

        co2_per_yr = get_yearly_totals(user_id)

        if co2_per_yr.get(this_year):
            trees_to_offset = int(round(
                co2_per_yr[this_year]["yr_projected"] / TREE_POUNDS_CO2_PER_YEAR))
        else:
            trees_to_offset = 0

        return render_template("homepage.html",
                               years=sorted(years, reverse=True),
                               makes=makes, usercars=usercars,
                               co2_per_yr=co2_per_yr, this_year=this_year,
                               trees=trees_to_offset)

    else:
        return render_template("login-register.html")


@app.route("/process-login", methods=["POST"])
def login_process():
    """Logs a user in with their email and password."""

    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()

    # If user exists and password is correct, render homepage
    if user and (user.password == password):
        # Add user_id to session cookie
        session["user_id"] = user.user_id

        flash('You were successfully logged in')
        return redirect("/")
    # If either email or password incorrect, show message to user.
    else:
        flash("This combination of username and password doesn't exist")
        return redirect("/")


@app.route("/process-signup", methods=["POST"])
def register_process():
    """Takes in four inputs via POST request and returns redirect to hompage.
    Adds new user to the database if they don't exist."""

    email = request.form.get("email")
    password = request.form.get("password")
    name = request.form.get("name")

    if (User.query.filter_by(email=email).all()) == []:
        new_user = User(email=email, password=password, name=name)

        db.session.add(new_user)
        db.session.commit()

        # Add user_id to session cookie
        user = User.query.filter_by(email=email).first()
        session["user_id"] = user.user_id

    else:
        flash("This user already exists. Please log in.")
        return redirect("/")

    return redirect("/")


@app.route("/logout", methods=["GET"])
def logout_process():
    """Logs out users and redirects to homepage."""

    del session["user_id"]
    flash('You were successfully logged out')
    return redirect("/")


###  User Profile #############################################################


@app.route("/profile", methods=["GET"])
def view_profile():
    """User profile page"""

    user_id = session.get("user_id")

    if user_id:
        name = User.query.get(user_id).name
        residences = Residence.query.filter_by(user_id=user_id).all()
        usercars = UserCar.query.filter_by(user_id=user_id).all()

        makes = Car.get_unique_makes()

        return render_template("profile.html", residences=residences, name=name,
                               usercars=usercars, makes=makes)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/add-residence", methods=["POST"])
def add_residence():
    """Add a residence for a profile"""

    name_or_address = request.form.get("residence_name")
    zipcode = request.form.get("zipcode")
    number_of_residents = request.form.get("residents")
    user_id = session.get("user_id")
    is_default = request.form.get("default")

    if is_default is None:
        is_default = False

    Residence.create(user_id, zipcode, name_or_address, is_default,
                     number_of_residents)

    return redirect("/profile")


@app.route("/edit-residence", methods=["POST"])
def edit_residence():
    """Edit a residence in a profile"""

    user_id = session.get("user_id")
    residence_id = request.form.get("residence_id")
    name_or_address = request.form.get("residence_name")
    zipcode = request.form.get("zipcode")
    number_of_residents = request.form.get("residents")
    is_default = request.form.get("default")

    edited_residence = Residence.query.get(residence_id)

    if is_default is None:
        is_default = False

    current_residences = Residence.query.filter_by(user_id=user_id).all()

    if is_default:
        for residence in current_residences:
            residence.is_default = False

    edited_residence.name_or_address = name_or_address
    edited_residence.zipcode = zipcode
    edited_residence.number_of_residents = number_of_residents
    edited_residence.is_default = is_default

    db.session.commit()

    return redirect("/profile")


@app.route("/add-car", methods=["POST"])
def add_car():
    """Add a residence for a profile"""

    make = request.form.get("make")
    model = request.form.get("model")
    year = int(request.form.get("year"))
    cylinders = request.form.get("cylinders")
    transmission = request.form.get("transmission")
    is_default = request.form.get("default")
    user_id = session.get("user_id")

    # If default checkbox not checked, set value to False instead of None
    if is_default is None:
        is_default = False
    else:
        is_default = True

    UserCar.create(user_id, make, model, year, cylinders, transmission,
                   is_default)

    return redirect("/profile")


@app.route("/car-data", methods=["GET"])
def get_car_data():
    """Get list of unique cars given make, model, and year."""

    make = request.args.get('make')
    model = request.args.get('model')
    year = request.args.get('year')
    cylinders = request.args.get('cylinders')
    transmission = request.args.get('transmission')

    query = db.session.query(Car.make, Car.model, Car.year, Car.cylinders,
                             Car.transmission)

    # applies filters to the query based on what values the user has inputed
    if make:
        query = query.filter(Car.make == make).distinct()

    if model:
        query = query.filter(Car.model == model).distinct()

    if year:
        query = query.filter(Car.year == year).distinct()

    if cylinders:
        query = query.filter(Car.cylinders == cylinders).distinct()

    if transmission:
        query = query.filter(Car.transmission == transmission).distinct()

    models = []

    # creates a list of dictionaries
    for car_tuple in query.all():
        car_dict = {}
        car_dict["make"] = car_tuple[0]
        car_dict["model"] = car_tuple[1]
        car_dict["year"] = car_tuple[2]
        car_dict["cylinders"] = car_tuple[3]
        car_dict["transmission"] = car_tuple[4]
        models.append(car_dict)

    return jsonify(models)


###  Electricity Data #########################################################

@app.route("/kwh-log", methods=["GET"])
def view_kwh_log():
    """Lists all kwh the user has entered. User can enter and edit data on this
    page."""

    user_id = session.get("user_id")

    if user_id:

        electricity_logs = ElectricityLog.query.filter(
            ElectricityLog.residence.has(Residence.user_id == user_id)
            ).order_by(ElectricityLog.start_date.desc()).all()

        residences = Residence.query.filter_by(user_id=user_id).order_by(
            Residence.is_default.desc(), Residence.residence_id.desc()).all()

        if electricity_logs:
            summary = ElectricityLog.get_electricity_summary(user_id)
        else:
            summary = None

        years = reversed(ElectricityLog.get_kwh_years(user_id))

        return render_template("kwh-list.html",
                               electricity_logs=electricity_logs,
                               residences=residences,
                               summary=summary,
                               years=years)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/add-kwh", methods=["POST"])
def add_kwh():
    """User kwh data for the user."""

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    kwh = request.form.get("kwh")
    name_or_address = request.form.get("residence")
    user_id = session.get("user_id")

    try:
        residence = Residence.query.filter_by(user_id=user_id,
                                              name_or_address=name_or_address).one()
    except NoResultFound:  # .one() error
        residence = Residence.query.filter_by(user_id=user_id,
                                              name_or_address=name_or_address).first()

    residence_id = residence.residence_id

    new_kwh = ElectricityLog(start_date=start_date, end_date=end_date, kwh=kwh,
                             residence_id=residence_id)

    db.session.add(new_kwh)
    db.session.commit()

    return redirect("/kwh-log")


@app.route("/edit-kwh", methods=["POST"])
def edit_kwh():
    """Edit a kwh electricity log."""

    elect_id = request.form.get("elect_id")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    kwh = request.form.get("kwh")
    name_or_address = request.form.get("residence")
    residence_id = Residence.query.filter_by(
        name_or_address=name_or_address).one().residence_id

    edited_kwh = ElectricityLog.query.get(elect_id)

    edited_kwh.start_date = start_date
    edited_kwh.end_date = end_date
    edited_kwh.kwh = kwh
    edited_kwh.residence_id = residence_id

    db.session.commit()

    return redirect("/kwh-log")


###  Natural Gas Data #########################################################

@app.route("/ng-log", methods=["GET"])
def view_ng_log():
    """Lists all kwh the user has entered. User can enter and edit data on this
    page."""

    user_id = session.get("user_id")

    if user_id:

        ng_logs = NGLog.query.filter(
            NGLog.residence.has(Residence.user_id == user_id)
            ).order_by(NGLog.start_date.desc()).all()

        residences = Residence.query.filter_by(user_id=user_id).order_by(
            Residence.is_default.desc(), Residence.residence_id.desc()).all()

        if ng_logs:
            summary = NGLog.get_ng_summary(user_id)
        else:
            summary = None

        years = reversed(NGLog.get_ng_years(user_id))

        return render_template("ng-list.html",
                               ng_logs=ng_logs,
                               residences=residences,
                               summary=summary,
                               years=years)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/add-ng", methods=["POST"])
def add_ng():
    """Add natural gas data for the user."""

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    therms = request.form.get("therms")
    name_or_address = request.form.get("residence")
    user_id = session.get("user_id")

    residence = Residence.query.filter_by(user_id=user_id,
                                          name_or_address=name_or_address).one()

    residence_id = residence.residence_id

    new_therms = NGLog(start_date=start_date, end_date=end_date,
                       therms=therms, residence_id=residence_id)

    db.session.add(new_therms)
    db.session.commit()

    return redirect("/ng-log")


@app.route("/edit-ng", methods=["POST"])
def edit_ng():
    """Edit a natural gas log."""

    ng_id = request.form.get("ng_id")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    therms = request.form.get("therms")
    name_or_address = request.form.get("residence")
    residence_id = Residence.query.filter_by(
        name_or_address=name_or_address).one().residence_id

    edited_ng = NGLog.query.get(ng_id)

    edited_ng.start_date = start_date
    edited_ng.end_date = end_date
    edited_ng.therms = therms
    edited_ng.residence_id = residence_id

    db.session.commit()

    return redirect("/ng-log")


###  Trip Data ################################################################

@app.route("/trip-log", methods=["GET"])
def view_trip_log():
    """Lists all trips the user has entered. User can enter and edit data on
    this page."""

    user_id = session.get("user_id")

    if user_id:

        trip_logs = TripLog.query.filter_by(user_id=user_id).order_by(
            TripLog.date.desc(), TripLog.trip_id).all()

        usercars = UserCar.query.filter_by(user_id=user_id).order_by(
            UserCar.is_default.desc(), UserCar.usercar_id.desc()).all()

        # pre-load all of the avgerage co2 factors for the usercars
        avg_grams_co2_mile_factors = {}
        for usercar in usercars:
            if not avg_grams_co2_mile_factors.get(usercar.usercar_id):
                avg_grams_co2_mile_factors[usercar.usercar_id] = \
                    usercar.calculate_avg_grams_co2_mile()

        # calculate co2 for each trip the user has entered
        trip_co2s = []
        for trip in trip_logs:
            avg_grams_co2_mile_factor = avg_grams_co2_mile_factors[trip.usercar_id]
            co2 = trip.co2_calc(avg_grams_co2_mile_factor)
            trip_co2s.append(co2)

        # combine the trip objects with the co2 results for passing into jinja
        trips_and_co2 = zip(trip_logs, trip_co2s)

        if trip_logs:
            summary = TripLog.get_trip_summary(user_id)
        else:
            summary = None

        years = reversed(TripLog.get_trip_years(user_id))

        return render_template("trip-list.html",
                               trip_logs=trips_and_co2,
                               usercars=usercars,
                               summary=summary,
                               years=years)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/add-trip", methods=["POST"])
def add_trip():
    """Add transportation data for the user."""

    date = request.form.get("date")
    miles = float(request.form.get("miles"))
    usercar_id = request.form.get("car")
    is_roundtrip = request.form.get("roundtrip")

    if is_roundtrip is None:
        is_roundtrip = False

    if is_roundtrip:
        miles = miles * 2

    user_id = session.get("user_id")

    TripLog.create(user_id, usercar_id, date, miles)

    return redirect("/trip-log")


@app.route("/edit-trip", methods=["POST"])
def edit_trip():
    """Edit transportation data entered by the user."""

    trip_id = request.form.get("trip_id")
    date = request.form.get("date")
    miles = float(request.form.get("miles"))
    usercar_id = request.form.get("car")

    edited_trip = TripLog.query.get(trip_id)

    edited_trip.date = date
    edited_trip.miles = miles
    edited_trip.usercar_id = usercar_id

    db.session.commit()

    return redirect("/trip-log")


@app.route("/get-distance", methods=["GET"])
def get_distance():
    """Get the distance from google distance matrix api based on the origin
    and destination entered by the user"""

    origin = request.args.get('origin')
    destination = request.args.get('destination')
    api_key = os.environ['GOOGLE_API_KEY']

    payload = {"units": "imperial",
               "origins": origin,
               "destinations": destination,
               "key": api_key,
               "mode": "driving"
               }

    r = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json?",
                     params=payload)

    distance_info = r.json()

    # Gets the distance value from the returned JSON

    ## either add in a try/except use .get() to make better error messages and so
    # server doesn't fail
    distance_meters = distance_info["rows"][0]["elements"][0]["distance"]["value"]
    meters_to_miles = 0.00062137  # 0.00062137 miles in 1 meter
    distance_miles = distance_meters * meters_to_miles

    return str(round(distance_miles, 2))


###  Homepage Charts ##########################################################

@app.route("/year-comparison-json", methods=["GET"])
def get_year_comparison_data():

    user_id = session.get("user_id")

    years = [2017, 2016, 2015, 2014]
    this_year = date.today().year
    days_this_year = days_btw_today_and_jan1()

    trip_co2 = TripLog.get_co2_per_yr(user_id)
    kwh_co2 = ElectricityLog.get_co2_per_yr(user_id)
    ng_co2 = NGLog.get_co2_per_yr(user_id)

    co2_per_yr = []

    for year in years:
        total = 0
        if trip_co2.get(year):
            total += trip_co2[year]["total"]
        if kwh_co2.get(year):
            total += kwh_co2[year]["total"]
        if ng_co2.get(year):
            total += ng_co2[year]["total"]

        if year != this_year:
            co2_per_yr.append(round(total, 2))
        else:
            yr_projected = round(total / days_this_year, 2) * 365
            co2_per_yr.append(yr_projected)

    return jsonify(co2_per_yr)


@app.route("/co2-per-datatype.json", methods=["GET"])
def get_co2_per_datatype():

    user_id = session.get("user_id")
    year = request.args.get("year")

    start_date = "1/1/1900"
    end_date = "1/1/2036"

    if year != "ALL YEARS":
        start_date = "1/1/%s" % (year)
        end_date = "12/31/%s" % (year)

    trip_co2 = TripLog.sum_trip_co2(user_id, start_date, end_date)
    kwh_co2 = ElectricityLog.sum_kwh_co2(user_id, start_date, end_date)
    ng_co2 = NGLog.sum_ng_co2(user_id, start_date, end_date)

    return jsonify([trip_co2, kwh_co2, ng_co2])


@app.route("/co2-trend.json", methods=["GET"])
def get_co2_trend():
    """Calculate the monthly CO2 for each CO2 source for a given year and
    return as json."""

    user_id = session.get("user_id")
    year = request.args.get("year")

    months = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30,
              10: 31, 11: 30, 12: 31}

    months = sorted(months.items())
    trip_co2_per_month = []
    kwh_co2_per_month = []
    ng_co2_per_month = []

    for month in months:
        start_date = "%s/1/%s" % (month[0], year)
        end_date = "%s/%s/%s" % (month[0], month[1], year)
        trip_co2_per_month.append(
            TripLog.sum_trip_co2(user_id, start_date, end_date))
        kwh_co2_per_month.append(
            ElectricityLog.sum_kwh_co2(user_id, start_date, end_date))
        ng_co2_per_month.append(
            NGLog.sum_ng_co2(user_id, start_date, end_date))

    return jsonify({"trip": trip_co2_per_month,
                    "kwh": kwh_co2_per_month,
                    "ng": ng_co2_per_month})


@app.route("/co2-other-location.json", methods=["GET"])
def get_co2_other_location():
    """Calculate the kwh CO2 for the user's current residence and as well as the
    potential CO2 at a different location and return as JSON."""

    user_id = session.get("user_id")
    year = request.args.get("year")
    zipcode = request.args.get("zipcode")

    months = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30,
              10: 31, 11: 30, 12: 31}

    months = sorted(months.items())

    kwh_co2_per_month = []
    kwh_co2_per_month_other_location = []

    if datetime.now().year == int(year):
        days = days_btw_today_and_jan1()
    else:
        days = 365

    for month in months:
        start_date = "%s/1/%s" % (month[0], year)
        end_date = "%s/%s/%s" % (month[0], month[1], year)

        # CO2 per month
        kwh_co2_per_month.append(
            ElectricityLog.sum_kwh_co2(user_id, start_date, end_date))
        kwh_co2_per_month_other_location.append(
            ElectricityLog.sum_kwh_co2_other_location(user_id, zipcode,
                                                      start_date, end_date))

        # CO2 per day (rate)
        co2_daily_rate = round(sum(kwh_co2_per_month) / days, 2)
        co2_daily_rate_other_location = round(sum(
            kwh_co2_per_month_other_location) / days, 2)

        # Total CO2 for the year
        kwh_co2_per_year = round(sum(kwh_co2_per_month), 2)
        kwh_co2_per_year_other_location = round(sum(
            kwh_co2_per_month_other_location), 2)

        # percent change = (current - new) / current * 100
        try:
            percent_change = int(abs(
                kwh_co2_per_year - kwh_co2_per_year_other_location
                ) / kwh_co2_per_year * 100)
        except ZeroDivisionError:
            percent_change = None

        if percent_change is None:
            statement = "There is no data for that year to compare."
        elif kwh_co2_per_year > kwh_co2_per_year_other_location:
            statement = "This location %s your carbon footprint by %s percent" \
                % ("decreases", percent_change)
        elif kwh_co2_per_year < kwh_co2_per_year_other_location:
            statement = "This location %s your carbon footprint by %s percent" \
                % ("increases", percent_change)
        elif kwh_co2_per_year == kwh_co2_per_year_other_location:
            statement = "This location doesn't change the carbon footprint"

    return jsonify({"current_monthly_co2": kwh_co2_per_month,
                    "new_monthly_co2": kwh_co2_per_month_other_location,
                    "current_yearly_co2": kwh_co2_per_year,
                    "new_yearly_co2": kwh_co2_per_year_other_location,
                    "current_daily_rate": co2_daily_rate,
                    "new_daily_rate": co2_daily_rate_other_location,
                    "comparison_statement": statement
                    })


@app.route("/get-zipcode", methods=["GET"])
def get_zipcode():
    """Get a viable zipcode for the city that the user enters."""

    city = request.args.get('city')
    state = request.args.get('state')
    api_key = os.environ['ZIP_CODE_API_KEY']

    params = {"api_key": api_key,
              "city": city,
              "state": state,
              }

    #  https://www.zipcodeapi.com/rest/<api_key>/city-zips.<format>/<city>/<state>
    url = "https://www.zipcodeapi.com/rest/{api_key}/city-zips.json/{city}/{state}".format(**params)
    print url

    r = requests.get(url)
    zipcode_info = r.json()

    zipcode = zipcode_info["zip_codes"][0]

    return zipcode


@app.route("/co2-other-car.json", methods=["GET"])
def get_co2_other_car():
    """Calculate the trip CO2 for the user's current car and as well as the
    potential CO2 at a different car and return as JSON."""

    user_id = session.get("user_id")
    trip_year = request.args.get("tripYear")
    usercar_id = request.args.get("userCarId")
    make = request.args.get("make")
    model = request.args.get("model")
    car_year = request.args.get("carYear")
    cylinders = request.args.get("cylinders")
    transmission = request.args.get("transmission")

    months = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30,
              10: 31, 11: 30, 12: 31}

    months = sorted(months.items())

    trip_co2_per_month = []
    trip_co2_per_month_other_car = []

    if datetime.now().year == int(trip_year):
        days = days_btw_today_and_jan1()
    else:
        days = 365

    for month in months:
        start_date = "%s/1/%s" % (month[0], trip_year)
        end_date = "%s/%s/%s" % (month[0], month[1], trip_year)

        # CO2 per month
        trip_co2_per_month.append(
            TripLog.sum_trip_co2(user_id, start_date, end_date, usercar_id))

        trip_co2_per_month_other_car.append(
            TripLog.sum_trip_co2_other_car(user_id, make, model, car_year,
                                           cylinders, transmission, start_date,
                                           end_date, usercar_id))
        # CO2 per day (rate)
        co2_daily_rate = round(sum(trip_co2_per_month) / days, 2)
        co2_daily_rate_other_car = round(sum(
            trip_co2_per_month_other_car) / days, 2)

        # Total CO2 for the year
        trip_co2_per_year = round(sum(trip_co2_per_month), 2)
        trip_co2_per_year_other_car = round(sum(
            trip_co2_per_month_other_car), 2)

        # percent change = (current - new) / current * 100
        try:
            percent_change = int(abs(
                trip_co2_per_year - trip_co2_per_year_other_car
                ) / trip_co2_per_year * 100)
        except ZeroDivisionError:
            percent_change = None

        if percent_change is None:
            statement = "There is no data for that year to compare."
        elif trip_co2_per_year > trip_co2_per_year_other_car:
            statement = "This car %s your carbon footprint by %s percent" \
                % ("decreases", percent_change)
        elif trip_co2_per_year < trip_co2_per_year_other_car:
            statement = "This car %s your carbon footprint by %s percent" \
                % ("increases", percent_change)
        elif trip_co2_per_year == trip_co2_per_year_other_car:
            statement = "This car doesn't change the carbon footprint"

    return jsonify({"current_monthly_co2": trip_co2_per_month,
                    "new_monthly_co2": trip_co2_per_month_other_car,
                    "current_yearly_co2": trip_co2_per_year,
                    "new_yearly_co2": trip_co2_per_year_other_car,
                    "current_daily_rate": co2_daily_rate,
                    "new_daily_rate": co2_daily_rate_other_car,
                    "comparison_statement": statement
                    })


@app.route("/co2-day-of-week.json", methods=["GET"])
def get_co2_by_day_of_week():
    """Get the total CO2 for each day of the week from each source given a date
    range."""

    user_id = session.get("user_id")
    year = request.args.get("year")

    start_date = "1/1/%s" % (year)
    end_date = "12/31/%s" % (year)

    trip_co2_by_day_of_week = TripLog.calculate_total_co2_per_day_of_week(
        user_id, start_date, end_date)

    kwh_co2_by_day_of_week = ElectricityLog.calculate_total_co2_per_day_of_week(
        user_id, start_date, end_date)

    return jsonify({"trip": trip_co2_by_day_of_week.values(),
                    "kwh": kwh_co2_by_day_of_week.values()})


###  Helper Functions #########################################################

TREE_POUNDS_CO2_PER_YEAR = 48


def days_btw_today_and_jan1():
    now = datetime.now()
    today = date(now.year, now.month, now.day)
    jan_first = date(now.year, 1, 1)

    return (today - jan_first).days


def get_yearly_totals(user_id):

    years = set()
    years.update(TripLog.get_trip_years(user_id),
                 ElectricityLog.get_kwh_years(user_id),
                 NGLog.get_ng_years(user_id)
                 )
    this_year = date.today().year
    days_this_year = days_btw_today_and_jan1()

    trip_co2 = TripLog.get_co2_per_yr(user_id)
    kwh_co2 = ElectricityLog.get_co2_per_yr(user_id)
    ng_co2 = NGLog.get_co2_per_yr(user_id)

    co2_per_yr = {}

    for year in years:
        total = 0
        if trip_co2.get(year):
            total += trip_co2[year]["total"]
        if kwh_co2.get(year):
            total += kwh_co2[year]["total"]
        if ng_co2.get(year):
            total += ng_co2[year]["total"]

        if year != this_year:
            daily_avg = round(total / 365, 2)
            co2_per_yr[year] = {"total": round(total, 2),
                                "daily_avg": daily_avg}
        else:
            daily_avg = round(total / days_this_year, 2)
            co2_per_yr[year] = {"total": round(total, 2),
                                "daily_avg": daily_avg,
                                "yr_projected": daily_avg * 365}

    return co2_per_yr

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
