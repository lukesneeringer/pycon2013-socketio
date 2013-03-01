from __future__ import unicode_literals
from django.conf import settings
from pycon2013_socketio.chat.models import Room, Event
from redis import Redis
from socketio.namespace import BaseNamespace
import json
import random
import signal


class ChatNamespace(BaseNamespace):
    def initialize(self):
        # Initialize a Redis PubSub object.
        self.redis_pubsub = Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB),
            password=settings.REDIS_PASSWORD,
        ).pubsub()

        # Just in case, create a default user name.
        self.user_name = 'user_'
        for i in range(0, 8):
            self.user_name += random.choice('0123456789abcdef')

        # Keep a list of all of the rooms of which I am a member.
        # This is important because of how Redis' subscription mechanism works;
        #   subscribing is a one-shot deal. If you subscribe to "foo", and then
        #   later subscribe to "bar", the list of channels to which you are
        #   subscribed is: `["bar"]`, not `["foo", "bar"]`
        # We could set up our chat JavaScript API to track this, and likely
        #   that would be better application design. However, that would cover
        #   over this gotcha instead of making it plain, so I'm tracking it
        #   here instead.
        self._subscribed_rooms = []

    def on_nick(self, user_name):
        """Set this connection's username."""

        self.user_name = user_name
        self.emit('nick_set', {
            'reason': 'Username set successfully.',    
        })

    def on_statement(self, room_slug, text):
        """Add the given statement to the chat room."""

        # First, ensure that the room_slug and message are not empty string.
        # If either is, then do nothing.
        if not room_slug or not text:
            return

        # Get the room.
        try:
            room = Room.objects.get(id=room_slug)
        except Room.DoesNotExist:
            self.emit('error', {
                'reason': 'Room %s does not exist.' % room_slug,
            })
            return

        # Create a new message object.
        Event.objects.create(
            message=text,
            event_type='statement',
            room=room,
            user_name=self.user_name,
        )

        # The message was posted successfully. Woo hoo!
        self.emit('statement_ok', {
            'reason': 'Message posted successfully.',    
        })

    def on_join(self, room_slug):
        """Connect to the given chat room.

        This involves subscribing this connection to receive all new chats in
        this particular room.
        """

        # First, retreive the chat room.
        # We're not being particularly interested in security, as this is
        #   only an example, so we're going to be extremely permissive about
        #   room existence and permissions.
        room, new = Room.objects.get_or_create(id=room_slug)

        # Stop the previous listener. We'll be spawning a new one
        #   once we subscribe to the new room.
        # Note: This has to come *before* we call subscribe, or strange
        #   things happen. General rule about `redis_pubsub.subscribe` and
        #   `redis_pubsub.listen` -- if you're listening, don't do anything
        #   else. If you need to change subscriptions, stop listening, change,
        #   and start listening again.
        if hasattr(self, '_greenlet'):
            self._greenlet.kill()

        # Now we "subscribe" to the room in Redis; this means that as
        #   notifications go through that Redis key, we'll hear about them
        #   (because `redis.listen()` is being run in our `self._listen`
        #   thread).
        # Note the comment above about subscription tracking -- we need to
        #   subscribe to *every* room in Redis that we're watching.
        if room.redis_key not in self._subscribed_rooms:
            self._subscribed_rooms.append(room.redis_key)
        self.redis_pubsub.subscribe(self._subscribed_rooms)

        # Now spawn a listener thread.
        # This is what will actually monitor Redis and send things down
        #   to the browser when Redis publishes.
        # In other words, this is what actually solves the "last mile
        #   problem".
        self._greenlet = self.spawn(self._listen)

        # Retrieve the previous events for this room.
        backlog = [dict(ev) for ev in Event.objects.filter(
            event_type__in=('statement', 'topic_set'),
            room=room,
        ).order_by('-created')[0:50]]
        backlog.reverse()  # I hate that `list.reverse` reverses in-place.

        # Create an event saying that we have joined the chat room.
        # N.B. This means that we will immediately receive this message,
        #   since we subscribed above.
        Event.objects.create(
            event_type='user_joined',
            room=room,
            user_name=self.user_name,
        )

        # Now send down a private success message.
        self.emit('room_joined', {
            'backlog': backlog,
            'reason': 'Joined room %s.' % room.id,
            'room': dict(room),
        })

    def on_topic(self, room_slug, text):
        """Change the topic of a given room."""

        # First, retreive the chat room.
        # We assume at this point that the room exists, and fail out if
        #   it does not.
        try:
            room = Room.objects.get(id=room_slug)
        except Room.DoesNotExist:
            self.emit('error', {
                'reason': 'Room %s does not exist.' % room_slug,
            })
            return

        # Okay, now actually alter the topic.
        # This involves two steps: altering the room topic, and sending
        #   an event saying that this has been done.
        # First we alter the room topic.
        room.topic = text
        room.save()

        # ...and now we send an event announcing the new topic.
        Event.objects.create(
            event_type='topic_set',
            message=text,
            room=room,
            user_name=self.user_name,
        )

        # And now our job here is done
        self.emit('topic_changed', {
            'reason': 'Topic successfully set on room %s.' % room.id,
            'room': dict(room),    
        })

    def on_leave(self, room_slug, announce_only=False):
        """Unsubscribe from a given chat room."""

        # First, retreive the chat room.
        # It only makes sense to unsubscribe from a room to which
        #   we are already subscribed, so if the room does not already
        #   exist, we error out.
        try:
            room = Room.objects.get(id=room_slug)
        except Room.DoesNotExist:
            self.emit('error', {
                'reason': 'Room %s does not exist.' % room_slug,
            })
            return

        # Okay, now create an event saying that this user
        # has left the room.
        Event.objects.create(
            event_type='user_left',
            room=room,
            user_name=self.user_name,
        )

        if not announce_only:
            # Remove the room from subscribed rooms.
            if room.redis_key in self._subscribed_rooms:
                ix = self._subscribed_rooms.index(room.redis_key)
                self._subscribed_rooms.pop(ix)

            # And now actually unsubscribe from the room.
            self.redis_pubsub.subscribe(self._subscribed_rooms)

            # Send back a private success notification.
            self.emit('room_left', {
                'reason': 'Left room %s.' % room.id,
                'room': dict(room),
            })

    def on_ping(self, *args):
        """A test method. Upon receiving this, it will send the same arguments
        back as a list."""

        self.emit('ping', *args)

    def recv_disconnect(self):
        """Upon disconnecting, declare the disconnection from each
        individual room."""

        # This is what happens if the client abruptly disconnects.
        # In this case, we want to state that the user has left the chat room,
        #   but there's no need to actually perform the disconnection because
        #   the connection has gone (or is going) away.
        # Therefore, just send the announcement.
        for redis_key in self._subscribed_rooms:
            room_slug = redis_key[5:]
            self.on_leave(room_slug, announce_only=True)

    def _despawn_all(self, *args):
        self.kill_local_jobs()

    def _listen(self):
        for block in self.redis_pubsub.listen():
            # Sanity Check: Is this a real block?
            if not block or 'data' not in block or not isinstance(
              block['data'], (str, unicode),
            ):
                continue

            # I am going to have a rule here that everything I send will
            #   be JSON, and their event name will be determined by the
            #   name of the room to which the event was posted.
            # From there, I will dispatch my events to the handlers I write
            #   for them as part of this class.
            data = json.loads(block['data'])
            if data and isinstance(data, dict):
                event_name = '%s_event' % data['room']
                self.emit(event_name, data)