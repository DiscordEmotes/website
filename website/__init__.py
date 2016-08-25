from flask import Flask, g, request
import os

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose

from .discord import User, Guild

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

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        user = User.current()
        return user and user.id in app.config['ADMIN_USER_IDS']

admin = Admin(app, name='Discord Emotes', template_mode='bootstrap3', index_view=CustomAdminIndexView())
migrate = Migrate(app, db)

if 'http://' in app.config['OAUTH2_REDIRECT_URI']:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

@app.before_request
def before_request():
    g.user = User.current()
    g.guilds = Guild.managed()

from . import views, models
