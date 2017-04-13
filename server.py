"""Carbon Calculator App"""

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash,
                   session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension
from model import (connect_to_db, db, User, Residence, ElectricityLog, NGLog,
                   UserCar, Car, TripLog)
from sqlalchemy.orm.exc import NoResultFound
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

        print years

        return render_template("homepage.html",
                               years=sorted(years, reverse=True))

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


@app.route("/logout", methods=["POST"])
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


###  kWh, NG, Trans Carbon Log ################################################

@app.route("/carbon-log", methods=["GET"])
def view_carbon_log():
    """Carbon data entry page."""

    user_id = session.get("user_id")

    if user_id:

        electricity_logs = ElectricityLog.query.filter(
            ElectricityLog.residence.has(Residence.user_id == user_id)).limit(5).all()

        ng_logs = NGLog.query.filter(
            NGLog.residence.has(Residence.user_id == user_id)).limit(5).all()

        trip_logs = TripLog.query.filter_by(user_id=user_id).limit(5).all()

        residences = Residence.query.filter_by(user_id=user_id).order_by(
            Residence.is_default.desc(), Residence.residence_id.desc()).all()

        usercars = UserCar.query.filter_by(user_id=user_id).order_by(
            UserCar.is_default.desc(), UserCar.usercar_id.desc()).all()

        return render_template("carbon-log.html",
                               electricity_logs=electricity_logs,
                               residences=residences,
                               ng_logs=ng_logs,
                               trip_logs=trip_logs,
                               usercars=usercars)

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

    return redirect("/carbon-log")


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

    return redirect("/carbon-log")


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

    return redirect("/carbon-log")


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

    return redirect("/carbon-log")


@app.route("/add-trip", methods=["POST"])
def add_trip():
    """Add transportation data for the user."""

    date = request.form.get("date")
    miles = float(request.form.get("miles"))
    usercar_id = request.form.get("car")

    user_id = session.get("user_id")

    TripLog.create(user_id, usercar_id, date, miles)

    return redirect("/carbon-log")


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

    return redirect("/carbon-log")


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


###  Viewing, Editing, Deleting Log Data ######################################


@app.route("/kwh-log", methods=["GET"])
def view_kwh_log():
    """Lists all kwh the user has entered. User can enter and edit data on this
    page."""

    user_id = session.get("user_id")

    if user_id:

        electricity_logs = ElectricityLog.query.filter(
            ElectricityLog.residence.has(Residence.user_id == user_id)
            ).order_by(ElectricityLog.start_date.desc()).all()

        return render_template("kwh-list.html",
                               electricity_logs=electricity_logs)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/ng-log", methods=["GET"])
def view_ng_log():
    """Lists all kwh the user has entered. User can enter and edit data on this
    page."""

    user_id = session.get("user_id")

    if user_id:

        ng_logs = NGLog.query.filter(
            NGLog.residence.has(Residence.user_id == user_id)
            ).order_by(NGLog.start_date.desc()).all()

        return render_template("ng-list.html",
                               ng_logs=ng_logs)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/trip-log", methods=["GET"])
def view_trip_log():
    """Lists all trips the user has entered. User can enter and edit data on
    this page."""

    user_id = session.get("user_id")

    if user_id:

        trip_logs = TripLog.query.filter_by(user_id=user_id).order_by(
            TripLog.date.desc(), TripLog.trip_id).all()

        return render_template("trip-list.html",
                               trip_logs=trip_logs)

    # return to homepage when not logged in
    else:
        return redirect("/")


###  Homepage Charts ##########################################################


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
        co2_daily_rate = round(sum(kwh_co2_per_month) / 365, 2)
        co2_daily_rate_other_location = round(sum(
            kwh_co2_per_month_other_location) / 365, 2)

        # Total CO2 for the year
        kwh_co2_per_year = round(sum(kwh_co2_per_month), 2)
        kwh_co2_per_year_other_location = round(sum(
            kwh_co2_per_month_other_location), 2)

        # percent change = (current - new) / current * 100
        try:
            percent_change = round(abs(
                kwh_co2_per_year - kwh_co2_per_year_other_location
                ) / kwh_co2_per_year * 100, 2)
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


###  Helper Functions #########################################################

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
