# Facebook app info
FACEBOOK_APP_ID = 1234567890  # TODO change
FACEBOOK_APP_SECRET = '0123456789abcdef'  # TODO change

# SQLAlchemy database URL. See http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls
SQLALCHEMY_DATABASE_URL = 'sqlite:////var/sqlite/fffeed.sqlite3'  # TODO change

# How many different change bundles to retrieve on the web app
WEB_APP_BUNDLE_LIMIT = 5

# HTTPAuth username and password (sha256 hashed) for the web app pages
WEB_APP_USERNAME = 'jane'  # TODO change
WEB_APP_PASSWORD_SHA256 = '799ef92a11af918e3fb741df42934f3b568ed2d93ac1df74f1b8d41a27932a6f'  # TODO change

# How many different change bundles to retrieve on the ATOM feed
ATOM_FEED_BUNDLE_LIMIT = 10

# ATOM locale (for date format, mostly)
ATOM_FEED_LOCALE = ('en_CA', 'UTF-8')

# A prefix path for the ATOM feed, to prevent people from guessing the path
# (This path is not protected using HTTPAuth since many feed readers can't use it)
ATOM_FEED_PREFIX = '/my_secret_path'  # TODO change
