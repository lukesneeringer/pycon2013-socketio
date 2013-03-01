from __future__ import unicode_literals
from gevent import monkey, spawn; monkey.patch_all()  # this *must* run first
from django.contrib.staticfiles.management.commands import runserver
from django.utils.autoreload import code_changed, restart_with_reloader
from optparse import make_option
from signal import SIGINT
from socketio.server import SocketIOServer
import django
import os
import subprocess
import sys
import time


# Make reload tracking that Django's original runserver has
# work; the SocketIO server piece breaks it otherwise.
_server_should_reload = False
def reload_watcher():
    global _server_should_reload
    while True:
        _server_should_reload = code_changed()
        if _server_should_reload:
            os.kill(os.getpid(), SIGINT)
        time.sleep(1)


class Command(runserver.Command):
    help = ' '.join((
        'Starts a lightweight socket.io server using gevent,',
        'which will also serve static files and non-socketIO things',
        'through the regular `runserver`, which is a superclass.',
    ))
    
    option_list = runserver.Command.option_list + (
        make_option('--host',
            default='127.0.0.1',
            dest='host',
            help='Designates the interface to listen on (default: 127.0.0.1).',
        ),
        make_option('--port',
            default=8000,
            dest='port',
            help=' '.join((
                'Designates the port to run the server (default: 8000).',
                'Note: The Flash policy server always runs on port 843.',
            )),
            type='int',
        ),
    )
    
    
    def handle(self, *args, **kwargs):
        """Run the websocket server."""
        
        # Set the settings module for the websocket server.
        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
        
        # Import the WSGI handler.
        application = self.get_handler(*args, **kwargs)
        
        # Print nice things to the console; make it look mostly like
        # the traditional Django dev server.
        print "Django version {version}, using settings '{settings}'.".format(
            settings=os.environ['DJANGO_SETTINGS_MODULE'],
            version=django.get_version(),
        )
        print ' '.join((
            'SocketIO server is listening on port %d' % kwargs['port'],
            'and on port 843 (Flash policy server).',
        ))
        print 'Quit the server with CONTROL-C.'
        
        # Create the SocketIO server.
        # Pay special attention here to the `resource` keyword argument.
        #   The SocketIO server will only do SocketIO connections on URIs
        #   starting with this resource. So, using "socket.io" as your
        #   resource means that the SocketIO server expects its special
        #   connections to come in at `http://domain.com/socket.io/foo/`.
        # The default on both the Python side and the JavaScript side
        #   is "socket.io", and this is probably the best choice. It's possible
        #   to use something else, but it has to match everywhere and most
        #   likely won't be very DRY unless you jump a lot of hoops.
        socket_io_server = SocketIOServer(
            (kwargs['host'], kwargs['port']),
            application,
            resource='socket.io',
            policy_server=True,
        )
        
        # Set up the socket io server to actually serve; use the
        # auto-reloader if desired.
        use_reloader = kwargs['use_reloader']
        if use_reloader:
            spawn(reload_watcher)
        
        # Run the socket.io server within a try/except block
        # (so that if it is shut down, it can be restarted).
        try:
            socket_io_server.serve_forever()
        except KeyboardInterrupt:
            global _server_should_reload
            if _server_should_reload:
                # Set my "should reload" variable back to False.
                _server_should_reload = False
                
                # Kill the server.
                socket_io_server.kill()
                socket_io_server = None
                
                # Now, reload a new server.
                print '\nReloading server...'
                restart_with_reloader()
            else:
                print '\r\n\n'
                sys.exit(0)