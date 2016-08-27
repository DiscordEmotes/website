from werkzeug.utils import secure_filename
from flask import session, request, g
from flask import render_template, flash
from flask import redirect, url_for, send_from_directory
from flask import Blueprint, current_app

from PIL import Image
import sys
import errno
import random
import os, hashlib

from .discord import make_session, DISCORD_AUTH_BASE_URL, DISCORD_TOKEN_URL
from .models import Emote, db
from .forms import EmoteUploadForm
from .utils import login_required, guild_admin_required

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html')

def get_auth_url():
    with make_session() as discord:
        url, state = discord.authorization_url(DISCORD_AUTH_BASE_URL)
        session['oauth2_state'] = state
        return url

@main.route('/login')
def login():
    return redirect(get_auth_url())

@main.route('/callback')
def callback():
    state = session.get('oauth2_state')
    if not state and request.values.get('error'):
        return redirect(url_for('.index'))

    with make_session(state=state) as discord:
        token = discord.fetch_token(DISCORD_TOKEN_URL,
                                    client_secret=current_app.config['OAUTH2_SECRET_KEY'],
                                    authorization_response=request.url)

        session['oauth2_token'] = token
        session.permanent = True
        return redirect(url_for('.guilds'))

@main.route('/guilds')
@login_required
def guilds():
    return render_template('guilds.html', title='My Servers')

@main.route('/guilds/<int:guild_id>')
@login_required
@guild_admin_required
def guild(guild_id):
    guild = g.managed_guild
    emotes = Emote.guild_emotes(guild_id)
    return render_template('guild.html', emotes=emotes, guild=guild, title=guild.name)

@main.route('/guilds/<int:guild_id>/emotes/<int:emote_id>', methods=['GET', 'POST'])
@guild_admin_required
def emote(guild_id, emote_id):
    emote = Emote.query.get(emote_id)

    # this check breaks when we allow shared emotes
    if emote is None or emote.owner_id != guild_id:
        abort(404)

    if request.method == 'POST':
        if 'toggle' in request.form:
            emote.shared = not emote.shared
            db.session.commit()
            flash('Emote updated.', 'is-success')
        elif 'delete' in request.form:
            db.session.delete(emote)
            db.session.commit()
            flash('Emote deleted.', 'is-success')
            return redirect(url_for('.guild', guild_id=guild_id))

    return render_template('emote.html', guild=g.managed_guild, emote=emote, title=emote.name)

@main.route('/guilds/<int:guild_id>/emotes/new', methods=['GET', 'POST'])
@login_required
@guild_admin_required
def add_emote(guild_id):
    emotes = Emote.guild_emotes(guild_id)

    form = EmoteUploadForm()
    if form.validate_on_submit():
        if len(emotes) >= 10:
            flash('You have already reached the maximum number of emotes for this server', 'is-danger')
            return redirect(request.url)

        if len(form.name.data) > 20:
            flash('The name of your emote must be 20 characters or less', 'is-danger')
            return redirect(request.url)

        try:
            image = Image.open(form.emote.data)
        except Exception as e:
            flash('Invalid image', 'is-danger')
            return redirect(request.url)

        ext = image.format
        if ext not in ('JPEG', 'PNG'):
            flash('Unsupported file extension (.%s).' % ext, 'is-danger')
            return redirect(request.url)

        if image.width > 128 or image.height > 128:
            flash('Image too big (got %sx%s and expected 128x128 or lower)' % (image.width, image.height), 'is-danger')
            return redirect(request.url)

        if image.format == "PNG":
            ext = "png"
        else:
            ext = "jpg"

        sha224 = hashlib.sha224(image.tobytes())
        hashed_filename = '{}.{}'.format(sha224.hexdigest(), ext)

        if hashed_filename in [e.filename for e in emotes]:
            flash('That image is already used for an emote. Choose another image.', 'is-danger')
            return redirect(request.url)

        emote = Emote(name=form.name.data,
                      owner_id=guild_id,
                      shared=form.shared.data,
                      filename=hashed_filename)

        try:
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], str(guild_id)))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], emote.path()))
        db.session.add(emote)
        db.session.commit()
        flash('Successfully uploaded emote.', 'is-success')
        return redirect(url_for('.guild', guild_id=guild_id))

    return render_template('add_emote.html', form=form, guild=g.managed_guild)

@main.route('/emotes/<int:guild_id>/<path:filename>')
def static_emote(guild_id, filename):
    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], str(guild_id)), filename)

@main.route('/library')
@main.route('/library/<int:page>')
def library(page=1):
    emotes = Emote.shared_emotes().paginate(page, int(current_app.config['EMOTES_PER_PAGE']), False)
    if not emotes.items and page != 1:
        abort(404)
    return render_template('library.html', title='Shared Library', emotes=emotes)
