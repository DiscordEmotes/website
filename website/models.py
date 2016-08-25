import os

from flask import current_app as app
from flask_sqlalchemy import SignallingSession
from sqlalchemy import event

from website import db
from .discord import send_message

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

def handle_deletes(session, flush_context):
    # Delete all emotes in session.dirty
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

@event.listens_for(Emote.verified, 'set')
def verified_set(target, value, oldvalue, initiator):
    # emote has become verified
    if oldvalue is False and value is True:
        send_message(target.owner_id, 'Emote "%s" has been verified and ready to use.' % target.name)
    elif oldvalue is True and value is False:
        send_message(target.owner_id, 'Emote "%s" has been unverified and can no longer be used.' % target.name)
