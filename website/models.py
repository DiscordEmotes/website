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
