## Make More Responsive Web Applications with SocketIO and gevent

This is a companion repository for the PyCon 2013 talk with the above title:

  * [Slides][1]
  * Video: PyVideo, [YouTube][3]

Its purpose is to provide a proof of concept. The code provided here was written
against Python 2.7, but it should work without issue on Python 2.6.

The primary, intended purpose of this repository is for it to be browsed ("how
do I do _that_?"), but you can install and run it, too.

### Dependencies

This package will depend on:

  * libevent
  * redis

...which you'll need to install on your own, either with your OS' package
manager or manually.

You'll also need to install the Python packages listed in
`pip-requirements.txt`, and the Python driver for your Django-supported
database of choice.

Note: This will almost certainly **not** work in Windows of any flavor.

### Redis

Note that this package does depend on Redis. Redis is not, by any means,
necessary to build a SocketIO-based application, and indeed, this demonstration
could work without it.

Adding Redis into the mix, however, makes it very straightforward to
have something outside of our web stack issue the broadcast. Since many use
cases will want to do this, it seems helpful to demonstrate it in this manner.

### Setup

Setup from this point _should_ be straightforward:

```
mkvirtualenv pycon2013_socketio --python=python2.7
workon pycon2013_socketio
git clone http://github.com/lukesneeringer/pycon2013-socketio.git
cd pycon2013-socketio/
pip install -r pip-requirements.txt
```

At this point, you'll need to do database setup:

  * Install the Python database driver for your Django-supported database
    of choice.
  * Create a database to house this project's tables.
  * Set the appropriate environment variables so Django knows credentials;
    consult `settings.py` for these.

Once the database is ready:

```
./manage.py syncdb
./manage.py runserver
```

Then point your browser at `http://localhost:8000/`.

  [1]: https://speakerdeck.com/pyconslides/make-more-responsive-web-applications-with-socketio-and-gevent-by-luke-sneeringer
  [3]: https://www.youtube.com/watch?v=9smvtUPmKNs
