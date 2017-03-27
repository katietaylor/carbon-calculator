"""Utility file to seed carbon_calc database."""

from sqlalchemy import func
from model import Region, Zipcode, Car
from model import connect_to_db, db
from server import app


def load_regions():
    """Load grid regions into database."""

    print "Regions"

    # Delete all rows in table, to avoid duplicates
    Region.query.delete()

    # Read region file and insert data
    for row in open("seed-data/regions.csv"):
        row = row.rstrip()
        region_id, name, lb_CO2e_MWh = row.split(",")

        region = Region(region_id=region_id, name=name, lb_CO2e_MWh=lb_CO2e_MWh)

        # Add to the session so the data will be stored
        db.session.add(region)

    # Commit the changes to the database
    db.session.commit()


def load_zipcodes():
    """Load zipcodes into database."""

    pass


def load_cars():
    """Load cars into database."""

    pass


if __name__ == "__main__":
    connect_to_db(app)

    # Call functions to import the
    load_regions()
