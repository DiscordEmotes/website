from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'app.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
app.config.from_object('config')

db = SQLAlchemy(app)

if 'http://' in app.config['OAUTH2_REDIRECT_URI']:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

from . import views, models
