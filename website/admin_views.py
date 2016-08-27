from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_admin import Admin, AdminIndexView, expose
from flask import flash, current_app, url_for
from jinja2 import Markup
from gettext import ngettext

from .models import Emote, db
from .discord import User

class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        user = User.current()
        return user and user.id in current_app.config['ADMIN_USER_IDS']

admin = Admin(name='Discord Emotes', template_mode='bootstrap3', index_view=CustomAdminIndexView())

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

            # .update() sucks
            emotes = Emote.query.filter(Emote.id.in_(new_ids)).all()
            for emote in emotes:
                emote.verified = True

            db.session.commit()

            flash(ngettext('Emote successfully verified.',
                           '%s emotes were successfully verified.' % len(emotes),
                           emotes))
        except Exception as e:
            if not self.handle_view_exception(e):
                raise

            flash('Failed to verify emotes. %s' % str(e), 'error')

    def is_accessible(self):
        user = User.current()
        return user and user.id in current_app.config['ADMIN_USER_IDS']

    def _filename_formatter(view, context, model, name):
        if not model.filename:
            return ''
        return Markup('<img style="width:32px;height:32px" src="%s">' % url_for('main.static_emote', guild_id=model.owner_id,
                                                                                filename=model.filename))

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
