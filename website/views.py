from website import app, make_session, get_current_user, DISCORD_AUTH_BASE_URL, DISCORD_TOKEN_URL
from flask import render_template, session, request, redirect, url_for

@app.route('/')
@app.route('/index')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/login')
def login():
    with make_session() as discord:
        url, state = discord.authorization_url(DISCORD_AUTH_BASE_URL)
        session['oauth2_state'] = state
        return redirect(url)

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
        return redirect(url_for('index'))
