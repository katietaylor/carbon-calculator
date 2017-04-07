"""Utility file to seed carbon_calc database."""

from sqlalchemy import func
from model import Region, Zipcode, Car, TransitType, ElectricityLog, NGLog
from model import connect_to_db, db
from server import app
import csv


def load_regions():
    """Load grid regions into database."""

    print "\n Regions \n"

    # Read region file and insert data
    for row in open("seed-data/regions.csv"):
        row = row.rstrip()
        region_id, name, lb_co2e_mega_wh = row.split(",")

        region = Region(region_id=region_id, name=name,
                        lb_co2e_mega_wh=lb_co2e_mega_wh)

        # Add to the session so the data will be stored
        db.session.add(region)

    # Commit the changes to the database
    db.session.commit()


def load_zipcodes():
    """Load zipcodes into database."""

    print "\n Zipcodes \n"

    # Read zipcode file and insert data
    for row in open("seed-data/zipcode-regions.csv"):
        row = row.rstrip()
        zipcode_id, state, region_id, secondary_region_id, tertiary_region_id \
            = row.split(",")

        zipcode = Zipcode(zipcode_id=zipcode_id, region_id=region_id)

        # Add to the session so the data will be stored
        db.session.add(zipcode)

    # Commit the changes to the database
    db.session.commit()


def load_cars():
    """Load cars into database."""

    print "\n Load Cars \n"

    with open('seed-data/vehicles.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            car = Car(car_id=row["id"],  # vehicle id
                      make=row["make"],  # manufacturer
                      model=row["model"],  # carline
                      fuel_type=row["fuelType1"],  # primary fuel
                      year=row["year"],  # model year
                      cylinders=row["cylinders"],
                      drive=row["drive"],
                      eng_id=row["engId"],
                      eng_description=row["eng_dscr"],
                      displacement=row["displ"],  # engine displacement in liters
                      trans_description=row["trans_dscr"],  # transmission descriptor
                      transmission=row["trany"],
                      grams_co2_mile=row["co2TailpipeGpm"],  # tailpipe CO2
                      mpg_street=row["city08"],  # city MPG for fuelType1
                      mpg_hw=row["highway08"],  # highway MPG for fuelType1
                      mpg_combo=row["comb08"],  # combined MPG for fuelType1
                      )

            # Add to the session so the data will be stored
            db.session.add(car)

    # Commit the changes to the database
    db.session.commit()


def load_daily_kwh(residence_id, csv_file):
    """Load kwh into database."""

    print "\n Load kwh \n"

    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        kwh_data = {}
        for row_dict in reader:
            date = row_dict["DATE"]
            usage = float(row_dict["USAGE"])

            kwh_data[date] = kwh_data.get(date, 0) + usage

        for date in kwh_data:
            elect_log = ElectricityLog(residence_id=residence_id,
                                       kwh=kwh_data[date],
                                       start_date=date,
                                       end_date=date
                                       )
            db.session.add(elect_log)
    db.session.commit()


def load_daily_ng(residence_id, csv_file):
    """Load ng into database."""

    print "\n Load Natural Gas \n"

    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        ng_data = {}
        for row_dict in reader:
            date = row_dict["DATE"]
            usage = float(row_dict["USAGE"])

            ng_data[date] = ng_data.get(date, 0) + usage

        for date in ng_data:
            ng_log = NGLog(residence_id=residence_id,
                           therms=ng_data[date],
                           start_date=date,
                           end_date=date
                           )
            db.session.add(ng_log)
    db.session.commit()


def load_bill_ng(residence_id, csv_file):
    """Load ng into database."""

    print "\n Load Natural Gas \n"

    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ng_log = NGLog(residence_id=residence_id,
                           therms=row["USAGE"],
                           start_date=row["START DATE"],
                           end_date=row["END DATE"]
                           )
            db.session.add(ng_log)
    db.session.commit()


def load_transit_type():
    """Load transportation types into the database."""

    print "\n Load Tranporation types \n"

    car = TransitType(transit_type='car')
    db.session.add(car)
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # Call functions to import the data
    load_regions()
    load_zipcodes()
    load_cars()
    load_transit_type()
    # load_daily_kwh(1, "seed-data/PGEData/pge_electric_interval_data_2078453646_2011-12-31_to_2017-04-01.csv")
    # load_bill_ng(1, "seed-data/PGEData/pge_gas_billing_data_2078453600_2010-07-15_to_2017-03-13.csv")
