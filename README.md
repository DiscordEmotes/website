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

SECRET_KEY = OAUTH2_SECRET_KEY
```
