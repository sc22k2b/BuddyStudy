from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

csrf = CSRFProtect(app)

migrate = Migrate(app, db, render_as_batch=True)

import logging
logging.basicConfig(level=logging.DEBUG)

admin = Admin(app, template_mode='bootstrap4')
from app import views, models