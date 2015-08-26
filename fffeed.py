import locale
from datetime import datetime

from collections_extended import bag
import facepy
from flask import Flask, abort, jsonify, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.contrib.atom import AtomFeed, FeedEntry

import auth
import settings


FACEBOOK_API_BASE_URL = 'https://graph.facebook.com/v2.2'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


class Variable(db.Model):
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return '<Variable %r>' % self.key


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Friend %r>' % self.name


class Change(db.Model):
    TYPE_ADDED = 'ADDED'
    TYPE_REMOVED = 'REMOVED'
    TYPE_INFO = 'INFO'
    TYPE_ERROR = 'ERROR'

    id = db.Column(db.Integer, primary_key=True)
    event_time = db.Column(db.DateTime)
    event_type = db.Column(db.String(255))
    event_content = db.Column(db.String(255))

    def __init__(self, event_time, event_type, event_content):
        self.event_time = event_time
        self.event_type = event_type
        self.event_content = event_content

    def __repr__(self):
        return '<Change %r: %r>' % (self.event_type, self.event_content)

    def dictify(self):
        return dict(id=self.id,
                    event_time=self.event_time.isoformat(),
                    event_type=self.event_type,
                    event_content=self.event_content)


@app.route('/')
@auth.requires_auth
def home():
    return render_template('home.html', facebook_app_id=settings.FACEBOOK_APP_ID)


@app.route(settings.ATOM_FEED_PREFIX + '/changes.atom')
def changes_feed():
    try:
        locale.setlocale(locale.LC_ALL, settings.ATOM_FEED_LOCALE)

        feed = AtomFeed(u"Recent changes to your Facebook friends list", feed_url=request.url, url=request.url_root)
        for change_bundle in get_changes(datetime.now(), settings.ATOM_FEED_BUNDLE_LIMIT):
            event_time = datetime.strptime(change_bundle['date'], '%Y-%m-%dT%H:%M:%S.%f')
            entry = FeedEntry(title=u"Changes for %s" % event_time.strftime('%A, %B %-d, %Y, %-I:%M %p'),
                              summary=unicode(render_template('feed.html', changes=change_bundle['changes'])),
                              summary_type='html',
                              url=request.url_root,
                              id='%s:%s' % (settings.ATOM_FEED_PREFIX, event_time.isoformat()),
                              updated=event_time,
                              author=u"FFFeed bot",
                              published=event_time,
                              feed_url=request.url)
            feed.add(entry)
        return feed.get_response()
    except Exception as e:
        jsonify(status=False, error='%r' % e)


@app.route('/ajax/access_token', methods=['POST'])
@auth.requires_auth
def ajax_access_token():
    try:
        short_access_token = request.form['access_token']
        graph = facepy.GraphAPI(short_access_token, url=FACEBOOK_API_BASE_URL)

        response = graph.get('/oauth/access_token',
                             grant_type='fb_exchange_token',
                             client_id=settings.FACEBOOK_APP_ID,
                             client_secret=settings.FACEBOOK_APP_SECRET,
                             fb_exchange_token=short_access_token)

        if not response.startswith('access_token='):
            raise facepy.FacebookError(response)

        long_access_token = response[len('access_token='):response.find('&')]

        db.session.merge(Variable(key='access_token', value=long_access_token))
        db.session.commit()

        return jsonify(success=True, access_token=long_access_token)
    except Exception as e:
        response = jsonify(success=False, error='%r' % e)
        response.status_code = 500
        return response


@app.route('/ajax/changes')
@auth.requires_auth
def ajax_changes():
    try:
        before = request.args.get('before', datetime.now())
        if isinstance(before, basestring):
            before = datetime.strptime(before, '%Y-%m-%dT%H:%M:%S.%f')

        change_bundles = get_changes(before, settings.WEB_APP_BUNDLE_LIMIT)
        if change_bundles:
            earliest_changes = datetime.strptime(change_bundles[-1]['date'], '%Y-%m-%dT%H:%M:%S.%f')

            more = db.session.query(Change).filter(Change.event_time < earliest_changes).count() > 0
        else:
            more = False

        return jsonify(success=True,
                       more=more,
                       change_bundles=change_bundles)
    except Exception as e:
        response = jsonify(success=False, error='%r' % e)
        response.status_code = 500
        return response


@app.route('/background/update')
def background_update():
    now = datetime.now()

    try:
        access_token = Variable.query.get('access_token')
        if access_token:
            access_token = access_token.value
        else:
            abort(403)

        previous_friends = bag((friend.name for friend in Friend.query.all()))

        graph = facepy.GraphAPI(access_token, url=FACEBOOK_API_BASE_URL)
        current_total_friends = graph.get('/me/friends')['summary']['total_count']

        current_friends = bag((friend['name'] for friend in graph.get('/me/taggable_friends')['data']))

        # Only create the friend-added Change events if this is not the first run
        if previous_friends:
            db.session.add_all(
                (Change(now, Change.TYPE_ADDED, friend) for friend in current_friends - previous_friends))
            db.session.add_all(
                (Change(now, Change.TYPE_REMOVED, friend) for friend in previous_friends - current_friends))
        else:
            db.session.add(Change(now, Change.TYPE_INFO, u"Started following your friends list here."))

        # Count the total number of friends
        total_friends_variable = Variable.query.get('total_friends') or Variable(key='total_friends', value='0')
        previous_total_friends = int(total_friends_variable.value)
        if 0 < previous_total_friends != current_total_friends:
            total_friends_variable.value = str(current_total_friends)
            db.session.merge(total_friends_variable)
            db.session.add(Change(now, Change.TYPE_INFO, u"Number of friends changed: %d\u2192%d." % (
                previous_total_friends, current_total_friends)))

        db.session.query(Friend).delete()
        db.session.add_all((Friend(friend) for friend in current_friends))

        db.session.commit()

        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        db.session.add(Change(now, Change.TYPE_ERROR, u"Error while running a background update. %r" % e))
        db.session.commit()

        response = jsonify(success=False, error='%r' % e)
        response.status_code = 500
        return response


def get_changes(before, bundle_limit):
    bundle_times = db.session.query(Change.event_time) \
        .filter(Change.event_time < before) \
        .order_by(desc(Change.event_time)) \
        .limit(bundle_limit) \
        .distinct()

    if not list(bundle_times):
        return []

    latest_changes, earliest_changes = bundle_times[0][0], bundle_times[-1][0]

    changes_flat = db.session.query(Change) \
        .filter(Change.event_time.between(earliest_changes, latest_changes)) \
        .order_by(desc(Change.event_time))

    change_bundles = {}
    for change in changes_flat:
        if change.event_time not in change_bundles:
            change_bundles[change.event_time] = []
        change_bundles[change.event_time].append(change.dictify())

    change_bundles = [dict(date=key.isoformat(), changes=change_bundles[key]) for key in
                      sorted(change_bundles.keys(), reverse=True)]

    return change_bundles


if __name__ == '__main__':
    app.run()
