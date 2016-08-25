from flask import session
from flask import current_app as app
from requests_oauthlib import OAuth2Session
import requests

from . import cache

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
        self.id = int(data.get('id'))
        self.discriminator = data.get('discriminator')
        self.email = data.get('email')
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
            data = cache.get_cached_user_data(token)
            if data is None:
                user = discord.get(DISCORD_API_URL + '/users/@me')
                if user.status_code == 401:
                    # our token is invalidated
                    session.pop('oauth2_token')
                    return None

                data = user.json()
                cache.set_cached_user_data(token, data)

            return cls(data) if data else None

    @property
    def avatar_url(self):
        if self.avatar is None:
            default = int(self.discriminator) % 5
            return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(default)
        return 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.jpg'.format(self)

class Guild:
    def __init__(self, data):
        self.id = int(data.get('id'))
        self.name = data.get('name')
        self.icon = data.get('icon')
        self.owner = data.get('owner')
        self.permissions = data.get('permissions')

    @classmethod
    def managed(cls):
        """Returns the Guilds that the current user has Manage Server on."""
        token = session.get('oauth2_token')
        if token is None:
            return []

        with make_session(token=token) as discord:
            servers = cache.get_cached_server_data(token)
            if servers is None:
                guilds = discord.get(DISCORD_API_URL + '/users/@me/guilds')
                if guilds.status_code != 200:
                    session.pop('oauth2_token')
                    return []

                data = guilds.json()
                cache.set_cached_server_data(token, data)

            else:
                data = servers

            ret = []

            for entry in data:
                # check if the user has MANAGE_GUILD in
                if entry['permissions'] & 0x00000020 == 0x00000020:
                    ret.append(cls(entry))

            return ret

    @property
    def icon_url(self):
        if self.icon is None:
            return None

        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)

def send_message(guild_id, content):
    token = app.config.get('BOT_TOKEN')
    if token is None:
        return

    headers = {
        'Authorization': 'Bot %s' % token,
    }
    url = '%s/channels/%s/messages' % (DISCORD_API_URL, guild_id)
    payload = {
        'content': str(content),
        'tts': False
    }
    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        return r.json()

    return None
