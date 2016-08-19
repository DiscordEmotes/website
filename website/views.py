from website import app
from flask import render_template, session, request, redirect, url_for, abort
from .discord import make_session, User, Guild, DISCORD_AUTH_BASE_URL, DISCORD_TOKEN_URL
from .models import Emote

@app.route('/')
@app.route('/index')
def index():
    user = User.current()
    guilds = Guild.managed()
    return render_template('index.html', user=user, guilds=guilds)

def get_auth_url():
    with make_session() as discord:
        url, state = discord.authorization_url(DISCORD_AUTH_BASE_URL)
        session['oauth2_state'] = state
        return url

@app.route('/login')
def login():
    return redirect(get_auth_url())

@app.route('/callback')
def callback():
    state = session.get('oauth2_state')
    if not state and request.values.get('error'):
        return redirect(url_for('index'))

    with make_session(state=state) as discord:
        token = discord.fetch_token(DISCORD_TOKEN_URL,
                                    client_secret=app.config['OAUTH2_SECRET_KEY'],
                                    authorization_response=request.url)

        session['oauth2_token'] = token
        session.permanent = True
        return redirect(url_for('guilds'))

@app.route('/guilds')
def guilds():
    user = User.current()
    if user is None:
        return redirect(get_auth_url())

    guilds = Guild.managed()
    return render_template('guilds.html', user=user, guilds=guilds, title='My Servers')

@app.route('/guilds/<int:guild_id>')
def guild(guild_id):
    user = User.current()
    guilds = Guild.managed()
    guild = next(filter(lambda g: g.id == guild_id, guilds), None)
    if guild is None:
        abort(404)

    emotes = Emote.guild_emotes(guild_id)
    return render_template('guild.html', user=user, emotes=emotes, guild=guild, title=guild.name)
