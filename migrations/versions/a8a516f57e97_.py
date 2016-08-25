"""Change filename type to actually match hash size.

Revision ID: a8a516f57e97
Revises: 02b220253f88
Create Date: 2016-08-24 22:34:42.941527

"""

# revision identifiers, used by Alembic.
revision = 'a8a516f57e97'
down_revision = '02b220253f88'

from alembic import op
import sqlalchemy as sa

# I had to do this one myself, thanks alembic

def upgrade():
    op.alter_column('emote', 'filename', existing_type=sa.String(32), type_=sa.String(60))

def downgrade():
    op.alter_column('emote', 'filename', existing_type=sa.String(60), type_=sa.String(32))
