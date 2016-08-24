from website import app, db, admin
from werkzeug.utils import secure_filename
from flask import render_template, session, request, redirect, url_for, abort, flash, send_from_directory
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from jinja2 import Markup
from PIL import Image
import sys
import errno
import random

from .discord import make_session, User, Guild, DISCORD_AUTH_BASE_URL, DISCORD_TOKEN_URL
from .models import Emote
from .forms import EmoteUploadForm

from gettext import ngettext
import os, hashlib

class EmoteView(ModelView):
    column_searchable_list = ['name', 'owner_id']
    column_filters = ['verified', 'shared']
    column_labels = {
        'owner_id': 'Guild ID',
        'filename': 'Emote'
    }

    @action('verify', 'Verify', 'Are you sure you want to verify the selected emotes?')
    def action_verify(self, ids):
        try:
            new_ids = [int(i) for i in ids]

            # TODO: potentially modify this to call some Emote.verify() function
            # that triggers a callback instead of calling update on filter
            query = Emote.query.filter(Emote.id.in_(new_ids)).update(dict(verified=True), synchronize_session='fetch')
            db.session.commit()
            flash(ngettext('Emote successfully verified.',
                           '%s emotes were successfully verified.' % query,
                           query))
        except Exception as e:
            if not self.handle_view_exception(e):
                raise

            flash('Failed to verify emotes. %s' % str(e), 'error')

    def is_accessible(self):
        user = User.current()
        return user and user.id in app.config['ADMIN_USER_IDS']

    def _filename_formatter(view, context, model, name):
        if not model.filename:
            return ''
        return Markup('<img style="width:32px;height:32px" src="%s">' % url_for('static_emote', guild_id=model.owner_id, filename=model.filename))

    def _bool_formatter(view, context, model, name):
        if getattr(model, name, False):
            return 'Yes'
        return 'No'

    column_formatters = {
        'filename': _filename_formatter,
        'shared': _bool_formatter,
        'verified': _bool_formatter
    }


admin.add_view(EmoteView(Emote, db.session))

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

@app.route('/guilds/<int:guild_id>/emotes/<int:emote_id>')
def emote(guild_id, emote_id):
    user = User.current()
    guilds = Guild.managed()
    guild = next(filter(lambda g: g.id == guild_id, guilds), None)
    if guild is None:
        abort(404)

    emotes = Emote.guild_emotes(guild_id)
    emote = next(filter(lambda e: e.id == emote_id, emotes), None)
    if emote is None:
        abort(404)
    return render_template('emote.html', user=user, emote=emote, guild=guild, title=emote.name)

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

        if len(form.name.data) > 20:
            flash('The name of your emote must be under 20 characters', 'is-danger')
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

        emote = Emote(name=form.name.data,
                      owner_id=guild_id,
                      shared=form.shared.data,
                      filename=hashed_filename)

        try:
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(guild_id)))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        image.save(os.path.join(app.config['UPLOAD_FOLDER'], emote.path()))
        db.session.add(emote)
        db.session.commit()
        flash('Successfully uploaded emote.', 'is-success')
        return redirect(url_for('guild', guild_id=guild_id))

    return render_template('add_emote.html', form=form, user=user, guild=guild)

@app.route('/emotes/<int:guild_id>/<path:filename>')
def static_emote(guild_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], str(guild_id)), filename)

@app.route('/library')
@app.route('/library/<int:page>')
def library(page=1):
    user = User.current()
    if not user:
        abort(404)
    emotes = Emote.shared_emotes().paginate(page, int(app.config['EMOTES_PER_PAGE']), False)
    if not emotes.items and page != 1:
        abort(404)
    return render_template('library.html', title='Shared Library', user=user, emotes=emotes)