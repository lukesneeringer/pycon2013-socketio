from __future__ import unicode_literals
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from pycon2013_socketio.chat.namespaces import ChatNamespace
from socketio import socketio_manage


def home(request):
    """Display a straightfoward template providing the simple
    chat interface."""

    return TemplateResponse(request, 'chat/home.html')


def socketio(request):
    """Handle SocketIO connections."""

    # If this isn't a socketio environment, fail now.
    if 'socketio' not in request.environ:
        return HttpResponseBadRequest(' '.join((
            '<h1>Bad Request</h1>',
            '<p>You are not a SocketIO connection.',
            'Go away and bother someone else.</p>',
        )))
        
    # Okay, now throw the SocketIO magic beans into the cauldron.
    # A few things to note here:
    #   * First, the URL routing within the /socket.io/ part is done here,
    #     so this is how the SocketIO manager routes /socket.io/chat/ to
    #     our ChatNamespace class over in the namespaces module.
    #   * Second, the third `request` argument is important. SocketIO does
    #     not depend on Django or on any other third-party framework, but
    #     we often need requests objects, and most Python web frameworks have
    #     some sort of similar concept. Sending something to that third
    #     positional argument is what will cause it to be available on our
    #     namespaces as `self.request`. If you don't have a request object
    #     or don't need one, you can skip this.
    try:
        socketio_manage(request.environ, {
            '/chat': ChatNamespace,
        }, request)
    except:
        logging.getLogger('socketio').error(
            'Exception while handling socketio connection',
            exc_info=True,
        )
                
    # we're done; send down an empty response
    return HttpResponse('')
