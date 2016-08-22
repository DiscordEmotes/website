import os

from flask import current_app as app
from flask_sqlalchemy import SignallingSession
from sqlalchemy import event

from website import db

class Emote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shared = db.Column(db.Boolean, index=True, nullable=False, default=False)
    owner_id = db.Column(db.BigInteger, index=True, nullable=False)
    name = db.Column(db.String(32), index=True, unique=True, nullable=False)
    verified = db.Column(db.Boolean, index=True, default=False)
    filename = db.Column(db.String(32))

    def __repr__(self):
        return '<Emote id={0.id} name={0.name} shared={0.shared}>'.format(self)

    @classmethod
    def guild_emotes(cls, guild_id):
        return cls.query.filter_by(owner_id=guild_id).all()

def handle_deletes(session, flush_context):
    # Delete all emotes in session.dirty
    for emote in session.deleted:
        if not isinstance(emote, Emote):
            continue

        filename = os.path.join(app.config['UPLOAD_FOLDER'], emote.filename)
        try:
            os.remove(filename)
        except OSError:
            continue

# register to SignallingSession instead of db.session otherwise an ArgumentError is raised
event.listen(SignallingSession, "after_flush", handle_deletes)
