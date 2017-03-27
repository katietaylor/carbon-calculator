"""Utility file to seed carbon_calc database."""

from sqlalchemy import func
from model import Region, Zipcode, Car, User, UserCar, TransitType, TransitLog, Residences, ElectricityLog, NGLog

from model import connect_to_db, db
# from server import app