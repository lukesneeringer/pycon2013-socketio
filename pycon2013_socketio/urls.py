from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from pycon2013_socketio.chat.namespaces import *

urlpatterns = patterns('pycon2013_socketio',
    url(r'^/?$', 'chat.views.home', name='home'),
    url(r'^socket\.io/', 'chat.views.socketio', name='socket.io'),
)