"""
Caching utilities
"""
import json

from flask import current_app

from werkzeug.contrib.cache import RedisCache


def get_redis():
    if not hasattr(current_app, 'redis'):
        host, port = current_app.config["REDIS_CONN"]
        cache = RedisCache(host, port, default_timeout=300)

        current_app.redis = cache

    return current_app.redis


def get_cached_user_data(token):
    # Gets cached user data.
    r = get_redis()
    key = "user" + json.dumps(token, sort_keys=True)
    d = r.get(key)
    if d:
        return json.loads(d)


def set_cached_user_data(token, data, expiration=300):
    r = get_redis()
    key = "user" + json.dumps(token, sort_keys=True)
    r.set(key, json.dumps(data), timeout=expiration)
    return data


def get_cached_server_data(token):
    r = get_redis()
    key = "server" + json.dumps(token, sort_keys=True)
    d = r.get(key)
    if d:
        return json.loads(d)


def set_cached_server_data(token, data, expiration=300):
    r = get_redis()
    key = "server" + json.dumps(token, sort_keys=True)
    r.set(key, json.dumps(data), timeout=expiration)
