"""
Caching utilities
"""
import json

import redis
from flask import current_app


def get_redis():
    if hasattr(current_app, "redis") and current_app.redis is not None:
        return current_app.redis

    host, port = current_app.config["REDIS_CONN"]
    current_app.redis = redis.StrictRedis(host=host, port=port)
    return current_app.redis


def get_cached_user_data(token):
    # Gets cached user data.
    r = get_redis()
    key = "user" + json.dumps(token)
    d = r.get(key)
    if d:
        return json.loads(d.decode())


def set_cached_user_data(token, data, expiration=300):
    r = get_redis()
    key = "user" + json.dumps(token)
    r.set(key, json.dumps(data), ex=expiration)
    return data


def get_cached_server_data(token):
    r = get_redis()
    key = "server" + json.dumps(token)
    d = r.get(key)
    if d:
        return json.loads(d.decode())


def set_cached_server_data(token, data, expiration=300):
    r = get_redis()
    key = "server" + json.dumps(token)
    r.set(key, json.dumps(data), ex=expiration)
