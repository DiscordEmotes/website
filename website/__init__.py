from flask import Flask, session
import os
from requests_oauthlib import OAuth2Session
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'app.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

db = SQLAlchemy(app)

if 'http://' in app.config['OAUTH2_REDIRECT_URI']:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

DISCORD_API_URL         = 'https://discordapp.com/api'
DISCORD_AUTH_BASE_URL   = DISCORD_API_URL + '/oauth2/authorize'
DISCORD_TOKEN_URL       = DISCORD_API_URL + '/oauth2/token'

def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None):
    client_id = app.config['OAUTH2_CLIENT_ID']
    secret = app.config['OAUTH2_SECRET_KEY']
    return OAuth2Session(client_id=app.config['OAUTH2_CLIENT_ID'],
                         token=token,
                         state=state,
                         scope=['identify', 'email', 'guilds'],
                         token_updater=token_updater,
                         auto_refresh_url=DISCORD_TOKEN_URL,
                         auto_refresh_kwargs={
                            'client_id': client_id,
                            'client_secret': secret
                         },
                         redirect_uri=app.config['OAUTH2_REDIRECT_URI'])

def get_current_user():
    token = session.get('oauth2_token')
    if token is None:
        return None

    with make_session(token=token) as discord:
        user = discord.get(DISCORD_API_URL + '/users/@me')
        if user.status_code == 401:
            # our token is invalidated
            session.pop('oauth2_token')
            return None

        return user.json() if user.status_code == 200 else None

from . import views, models
