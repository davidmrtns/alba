from alba import database, app
from alba.models import *


with app.app_context():
    database.create_all()
