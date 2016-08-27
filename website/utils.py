from functools import wraps
from flask import g, request, redirect, url_for, abort
from .models import Guild

def login_required(f):
    """Decorator that makes the view require logging in.

    If the user is not logged in, it redirects them to the index page.
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorator

def guild_admin_required(f):
    """Decorator that makes the view require guild admin privileges.

    A guild admin is someone that can edit the guild, e.g. MANAGE_GUILD or
    higher. This requires that the view defines a ``guild_id`` argument.

    After this decorator is used, ``g.managed_guild`` is set to the current
    managed guild.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        guild_id = request.view_args.get('guild_id')
        g.managed_guild = next(filter(lambda n: n.id == guild_id, g.guilds), None)
        if g.managed_guild is None:
            abort(404)
        return f(*args, **kwargs)

    return decorator

def public_guild_required(f):
    """Decorator that makes the view require a public guild.

    If the guild is not found or is not public then the view aborts
    with 404. The resulting guild is stored under ``g.guild``.

    Follows similar rules to :func:`guild_admin_required`.
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        guild_id = request.view_args.get('guild_id')

        # get the guild with the guild_id from our own guild list
        guild = next(filter(lambda s: s.id == guild_id, g.guilds), None)

        # if it isn't available, check if it's a public guild
        if guild is None:
            guild = Guild.query.get_or_404(guild_id)
            if guild.public is not True:
                abort(404)

        g.guild = guild
        return f(*args, **kwargs)
    return decorator
