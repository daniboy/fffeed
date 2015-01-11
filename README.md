Facebook Friends Feed
=====================

Keep track of changes to your Facebook friends list.

Facebook recently changed their API to prevent apps from accessing your friends list. This is a good thing for your
privacy (most apps that requested this information didn't provide you with any added benefit) but it does make it harder
to keep track of your friends list.

Using a workaround that asks facebook to provide a list of friends that you can tag in posts/pictures you can still get
an app to ask for (most*) of your friends list. The caveat of this workaround is that facebook manually tests and
approves (or more often, rejects) apps that ask for this permission. The good news is that if you create your own
facebook app and leave it in test mode while still using it personally!

\* Friends can choose to prevent others from tagging them, in which case they will not be tracked using this app


Deployment
----------

You can deploy FFFeed to your own server if it supports wsgi or any other method to
[deploy Flask](http://flask.pocoo.org/docs/0.10/deploying/).

### Create a Facebook app:

1. Go to [https://developers.facebook.com/apps/](https://developers.facebook.com/apps/) and choose *Add a New App*
2. Select *Web*, give it a name (such as “My `Facebook Friends Feed app”). Skip the Quick Start
3. Note the App ID and App Secret, you will use them later when deploying FFFeed to your own server
5. Choose Settings in the sidebar, add your *App Domain* (e.g. `[your-server].com`), then choose *+ Add Platform* and
type the full Site URL (e.g. `http://[your-server].com/`)

### Deploy FFFeed:
On your server:

1. [Create a virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) with Python 2.7.x and
`requirements.txt` (or install the requirements in your own environment)
2. Copy settings_SAMPLE.py to settings.py and change the required fields
3. Generate the database schema. If the database user that you choose in settings.py has permission to create tables:
using the console activate the virtualenv (e.g. `source /path/to/venv/bin/activate`) and run `python setup_db.py`. If
the user doesn't have permission to create tables, create them manually using the schema defined in `setup_db.sql`
4. Run the Flask app using [whichever method works best](http://flask.pocoo.org/docs/0.10/deploying/) for your case.
DreamHost has a [simple tutorial](http://wiki.dreamhost.com/Flask) for shared hosting.
5. Create a CRON job that will poll the background update service (e.g. every 24 hours). The URL is
`http://[your-server].com/background/update` and is not password protected.


Usage
-----

Navigate to the main page and log in with your facebook account to the app. If installed correctly, the app will now
start tracking changes to your facebook friends list.

The feed URL is `http://[your-server].com/[your-prefix]/changes.atom`.