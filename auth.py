from functools import wraps
import hashlib

from flask import Response, request

import settings


def check_auth(username, password):
    return username == settings.WEB_APP_USERNAME and hashlib.sha256(
        password).hexdigest() == settings.WEB_APP_PASSWORD_SHA256


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated