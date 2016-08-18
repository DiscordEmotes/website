from flask import session
from website import app
from requests_oauthlib import OAuth2Session
import requests

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

class User:
    def __init__(self, data):
        self.discriminator = data.get('discriminator')
        self.email = data.get('email')
        self.id = data.get('id')
        self.mfa_enabled = data.get('mfa_enabled')
        self.name = data.get('username')
        self.verified = data.get('verified', False)
        self.avatar = data.get('avatar')

    @classmethod
    def current(cls):
        """Returns the current User if applicable, None if not authenticated."""
        token = session.get('oauth2_token')
        if token is None:
            return None

        with make_session(token=token) as discord:
            user = discord.get(DISCORD_API_URL + '/users/@me')
            if user.status_code == 401:
                # our token is invalidated
                session.pop('oauth2_token')
                return None

            return cls(user.json()) if user.status_code == 200 else None

    @property
    def avatar_url(self):
        if self.avatar is None:
            default = int(self.discriminator) % 5
            return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(default)
        return 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.jpg'.format(self)
