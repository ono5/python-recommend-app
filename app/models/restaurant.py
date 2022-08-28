from sqlalchemy import Column, String, UniqueConstraint

from app.models.db import BaseDatabase, database


class Restaurant(BaseDatabase):
    __tablename__ = 'restaurant'
    name = Column(String)
    UniqueConstraint(name)

    @staticmethod
    def get_or_create(name):
        session = database.connect_db()
        row = session.query(Restaurant).filter(Restaurant.name == name).first()
        if row:
            session.close()
            # return exsiting data
            return row

        restaurant = Restaurant(name=name)
        session.add(restaurant)
        session.commit()
        session.close()

        # return restaurant data including ID
        row = session.query(Restaurant).filter(Restaurant.name == name).first()
        session.close()
        return row
