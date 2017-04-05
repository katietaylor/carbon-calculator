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
def login():
    """Renders login template if the user is not signed in and the homepage if
    the user is logged in."""

    if session.get("user_id"):
        return render_template("homepage.html")
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
    name = User.query.get(user_id).name

    if user_id:
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

    name_or_address = request.form.get("name_or_address")
    zipcode = request.form.get("zipcode")
    number_of_residents = request.form.get("no_residents")
    user_id = session.get("user_id")
    is_default = request.form.get("default")

    if is_default is None:
        is_default = False

    Residence.create(user_id, zipcode, name_or_address, is_default,
                     number_of_residents)

    return redirect("/profile")


@app.route("/add-car", methods=["POST"])
def add_car():
    """Add a residence for a profile"""

    make = request.form.get("make")
    model = request.form.get("model")
    year = int(request.form.get("year"))
    is_default = request.form.get("default")
    user_id = session.get("user_id")

    if is_default is None:
        is_default = False
    else:
        is_default = True

    print user_id, make, model, year, is_default, type(is_default)

    UserCar.create(user_id, make, model, year, is_default)

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

    # applies a filter to the query based on what values the user has inputed
    if make is not None:
        query = query.filter(Car.make == make).distinct()

    if model is not None and model:
        query = query.filter(Car.model == model).distinct()

    if year is not None and year:
        query = query.filter(Car.year == year).distinct()

    if cylinders is not None:
        query = query.filter(Car.cylinders == cylinders).distinct()

    if transmission is not None:
        query = query.filter(Car.transmission == transmission).distinct()

    models = []

    print "\n \n", query.all(), "\n \n"

    # creates a list of dictionaries
    for car_tuple in query.all():
        car_dict = {}
        car_dict["make"] = car_tuple[0]
        car_dict["model"] = car_tuple[1]
        car_dict["year"] = car_tuple[2]
        car_dict["cylinders"] = car_tuple[3]
        car_dict["transmission"] = car_tuple[4]
        models.append(car_dict)

    # models = [row.as_dict() for row in query.all()]

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
            UserCar.is_default.desc(), UserCar.user_car_id.desc()).all()

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
    except NoResultFound:  # one error
        residence = Residence.query.filter_by(user_id=user_id,
                                              name_or_address=name_or_address).first()

    residence_id = residence.residence_id

    new_kwh = ElectricityLog(start_date=start_date, end_date=end_date, kwh=kwh,
                             residence_id=residence_id)

    db.session.add(new_kwh)
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


@app.route("/add-trip", methods=["POST"])
def add_trip():
    """Add transportation data for the user."""

    date = request.form.get("date")
    miles = float(request.form.get("miles"))
    car = request.form.get("car").split("|")

    make = car[0]
    model = car[1]
    year = car[2]

    user_id = session.get("user_id")

    car_id = Car.query.filter_by(make=make, model=model, year=year).first().car_id

    TripLog.create(user_id, car_id, date, miles)

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

    print distance_info

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
            ElectricityLog.residence.has(Residence.user_id == user_id)).all()

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
            NGLog.residence.has(Residence.user_id == user_id)).all()

        return render_template("ng-list.html",
                               ng_logs=ng_logs)

    # return to homepage when not logged in
    else:
        return redirect("/")


@app.route("/trip-log", methods=["GET"])
def view_trip_log():
    """Lists all kwh the user has entered. User can enter and edit data on this
    page."""

    user_id = session.get("user_id")

    if user_id:

        trip_logs = TripLog.query.filter_by(user_id=user_id).all()

        return render_template("trip-list.html",
                               trip_logs=trip_logs)

    # return to homepage when not logged in
    else:
        return redirect("/")



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
