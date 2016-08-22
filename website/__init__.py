from flask import Flask
import os

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=2*1024*1024, # 2 MiB max upload
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'app.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
app.config.from_object('config')

app.config['UPLOAD_FOLDER'] = os.path.realpath(app.config['UPLOAD_FOLDER'])

try:
    os.makedirs(app.config['UPLOAD_FOLDER'])
except OSError:
    pass

db = SQLAlchemy(app)
admin = Admin(app, name='Discord Emotes', template_mode='bootstrap3')
migrate = Migrate(app, db)

if 'http://' in app.config['OAUTH2_REDIRECT_URI']:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

from . import views, models
