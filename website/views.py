from website import app, db
from werkzeug.utils import secure_filename
from flask import render_template, session, request, redirect, url_for, abort, flash
from .discord import make_session, User, Guild, DISCORD_AUTH_BASE_URL, DISCORD_TOKEN_URL
from .models import Emote
from .utils import get_image_size
from .forms import EmoteUploadForm
import os, hashlib

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

@app.route('/guilds/<int:guild_id>/emotes/new', methods=['GET', 'POST'])
def add_emote(guild_id):
    # TODO: @app.before_request this noise
    user = User.current()
    guilds = Guild.managed()
    guild = next(filter(lambda g: g.id == guild_id, guilds), None)
    if guild is None:
        abort(404)

    emotes = Emote.guild_emotes(guild_id)

    form = EmoteUploadForm()
    if form.validate_on_submit():
        if len(emotes) > 10:
            flash('You have already reached the maximum number of emotes for this server', 'is-danger')
            return redirect(request.url)

        filename = secure_filename(form.emote.data.filename)
        actual_filename, ext = os.path.splitext(filename)
        if ext.lower() not in ('.png', '.jpg', '.jpeg'):
            flash('Unsupported file extension (%s).' % ext, 'is-danger')
            return redirect(request.url)

        try:
            width, height = get_image_size(form.emote.data.stream)
        except Exception as e:
            flash('Unsupported image type or image is too big.', 'is-danger')
            return redirect(request.url)

        if width > 128 or height > 128:
            flash('Image too big (got %sx%s and expected 128x128 or lower)' % (width, height), 'is-danger')
            return redirect(request.url)

        md5 = hashlib.md5(actual_filename.encode('utf-8', 'backslashreplace'))
        hashed_filename = '{}{}'.format(md5.hexdigest(), ext)

        emote = Emote(name=form.name.data,
                      owner_id=guild_id,
                      shared=form.shared.data,
                      filename=hashed_filename)

        form.emote.data.seek(0)
        form.emote.data.save(os.path.join(app.config['UPLOAD_FOLDER'], hashed_filename))
        db.session.add(emote)
        db.session.commit()
        flash('Successfully uploaded emote.', 'is-success')
        return redirect(url_for('guild', guild_id=guild_id))

    return render_template('add_emote.html', form=form, user=user, guild=guild)
