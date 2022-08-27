import logging

from app.controllers.roboter import server
import settings

logging.basicConfig(filename=settings.LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("running server")
    server.start(debug=settings.DEBUG)

    # from app.models.db import database
    # from app.models.user import User
    # from app.models.restaurant import Restaurant
    # from app.models.rate import Rate
    # session = database.connect_db()
    # u = User()
    # u.name = "test"

    # r = Restaurant()
    # r.name = "test"

    # rate = Rate()
    # rate.user_id = 1
    # rate.restaurant_id = 1
    # rate.value = 5

    # session.add(u)
    # session.add(r)
    # session.add(rate)
    # session.commit()
    # session.close()
