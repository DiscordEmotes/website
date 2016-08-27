from flask import Flask, g
from flask_migrate import Migrate

import os

from . import views, models, admin_views, discord

migrate = Migrate(models.db)

def before_request():
    g.user = discord.User.current()
    g.guilds = discord.Guild.managed()

def create_app(conf):
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=2*1024*1024, # 2 MiB max upload
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    app.config.from_object(conf)

    app.config['UPLOAD_FOLDER'] = os.path.realpath(app.config['UPLOAD_FOLDER'])

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    if 'http://' in app.config['OAUTH2_REDIRECT_URI']:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

    app.before_request(before_request)

    # extension lazy init
    migrate.init_app(app)
    admin_views.admin.init_app(app)
    models.db.init_app(app)

    app.register_blueprint(views.main)
    return app
