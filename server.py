"""Carbon Calculator App"""

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash,
                   session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User, Residence
import profile

app = Flask(__name__)

app.secret_key = "ABC"  # Required to use Flask sessions and the debug toolbar
app.jinja_env.undefined = StrictUndefined  # Undefined variable in Jinja2 will raise an error.


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
        return render_template("homepage.html")
    # If either email or password incorrect, show message to user.
    else:
        flash("This combination of username and password doesn't exist")


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


@app.route("/profile", methods=["GET"])
def view_profile():
    """User profile page"""

    if session.get("user_id"):
        return render_template("profile.html")
    else:
        return redirect("/")


@app.route("/add-residence", methods=["POST"])
def add_residence():
    """User profile page"""

    address = request.form.get("address")
    zipcode = request.form.get("zipcode")
    number_of_residents = request.form.get("no_residents")
    is_default = request.form.get("default")
    user_id = session.get("user_id")

    profile.add_residence(user_id, zipcode, address, is_default,
                          number_of_residents)

    return redirect("/profile")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
