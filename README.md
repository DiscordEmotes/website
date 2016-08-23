This will be the coolest thing since sliced bread.

Maybe.

Probably not.

## Requirements

- Some undetermined python version
- Flask

Just do `pip install -r requirements.txt`.

## Running

Make a `config.py` file in the root directory with the following variables:

```py
OAUTH2_CLIENT_ID = 'my client ID'
OAUTH2_SECRET_KEY = 'my app secret'
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
UPLOAD_FOLDER = 'base directory for file uploads'

SECRET_KEY = OAUTH2_SECRET_KEY

ADMIN_USER_IDS = ['123456789123456789']
```

Next up do the following:

```
$ export FLASK_APP=run.py
$ export FLASK_DEBUG=1
$ python3 -m flask db upgrade
$ python3 -m flask run
```
