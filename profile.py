"""Profile functionality"""

from model import db, Residence


def add_residence(user_id, zipcode_id, address, is_default, number_of_residents):

    current_residences = Residence.query.filter_by(user_id=user_id).all()

    if is_default and current_residences:
        for residence in current_residences:
            residence.is_default = False

    new_residence = Residence(user_id=user_id, zipcode_id=zipcode_id,
                              address=address, is_default=is_default,
                              number_of_residents=number_of_residents)

    db.session.add(new_residence)
    db.session.commit()
