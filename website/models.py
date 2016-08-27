from flask import current_app as app
from flask_sqlalchemy import SignallingSession, SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.orm.unitofwork import UOWTransaction

import os

db = SQLAlchemy()
migrate = Migrate()

def send_message(guild_id, content):
    token = app.config.get('BOT_TOKEN')
    if token is None:
        return

    headers = {
        'Authorization': 'Bot %s' % token,
    }
    url = 'https://discordapp.com/api/v6/channels/%s/messages' % guild_id
    payload = {
        'content': str(content),
        'tts': False
    }
    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        return r.json()

    return None


class Emote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shared = db.Column(db.Boolean, index=True, nullable=False, default=False)
    owner_id = db.Column(db.BigInteger, index=True, nullable=False)
    name = db.Column(db.String(32), index=True, unique=True, nullable=False)
    verified = db.Column(db.Boolean, index=True, default=False)
    # SHA-224 is 224 bits, 4 bits per hex code means 224 / 4 = 56 characters
    # then we add 4 for the extension and we get a maximum of 60 characters.
    filename = db.Column(db.String(60))

    def __repr__(self):
        return '<Emote id={0.id} name={0.name} shared={0.shared}>'.format(self)

    @classmethod
    def guild_emotes(cls, guild_id):
        return cls.query.filter_by(owner_id=guild_id).all()

    @classmethod
    def shared_emotes(cls):
        return cls.query.filter_by(shared=True, verified=True)

    def path(self):
        return os.path.join(str(self.owner_id), self.filename)

class Guild(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    icon = db.Column(db.String)
    name = db.Column(db.String)
    public = db.Column(db.Boolean, default=True)

    @classmethod
    def upsert_from(cls, guilds):
        cached = {s.id: s for s in guilds}

        # updates
        update_mappings = []
        for existing in cls.query.filter(cls.id.in_(set(cached.keys()))).all():
            new_guild = cached[existing.id]
            mapping = {
                'id': existing.id,
                'name': new_guild.name,
                'icon': new_guild.icon
            }
            update_mappings.append(mapping)
            cached.pop(existing.id)

        # inserts
        insert_mappings = [
            {
                'id': guild.id,
                'name': guild.name,
                'icon': guild.icon
            }
            for guild in cached.values()
        ]

        db.session.bulk_update_mappings(cls, update_mappings)
        db.session.bulk_insert_mappings(cls, insert_mappings)
        db.session.commit()

    @property
    def icon_url(self):
        if self.icon is None:
            return None

        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)

def handle_verifies(session, flush_context: UOWTransaction):
    # Handles verification checking on emotes.
    for emote in session.dirty:
        if not isinstance(emote, Emote):
            # Ignore it
            continue

        history = inspect(emote).attrs.verified.history
        if history.added and history.added[0]:
            verified = True
        else:
            verified = False

        # TODO: Do whatever with the verified status.

def handle_deletes(session, flush_context):
    # Delete all emotes in session.deleted
    for emote in session.deleted:
        if not isinstance(emote, Emote):
            continue

        filename = os.path.join(app.config['UPLOAD_FOLDER'], emote.path())
        try:
            os.remove(filename)
        except OSError:
            pass

        send_message(emote.owner_id, 'Emote "%s" has been deleted and can no longer be used.' % emote.name)

# register to SignallingSession instead of db.session otherwise an ArgumentError is raised
event.listen(SignallingSession, "after_flush", handle_deletes)
event.listen(SignallingSession, "after_flush", handle_verifies)
