This will be the coolest thing since sliced bread.

Maybe.

Probably not.

## Requirements

- Some undetermined python version
- Flask
- A redis server
- Pillow

Just do `pip install -r requirements.txt`.

## Running

Make a `config.py` file in the root directory with the following variables:

```py
OAUTH2_CLIENT_ID = 'my client ID'
OAUTH2_SECRET_KEY = 'my app secret'
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
UPLOAD_FOLDER = 'base directory for file uploads'
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@127.0.0.1/database'

EMOTES_PER_PAGE = 20

SECRET_KEY = OAUTH2_SECRET_KEY

REDIS_CONN = ("127.0.0.1", 6379)

ADMIN_USER_IDS = [123456789123456789]
BOT_TOKEN = 'bot token here'
```

Make sure to create a PostgreSQL database and point the URI appropriately.

Next up do the following:

```
$ export FLASK_APP=run.py
$ export FLASK_DEBUG=1
$ python3 -m flask db upgrade
$ python3 -m flask run
```
