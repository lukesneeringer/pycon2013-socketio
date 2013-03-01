from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from redis import Redis
import json


class Room(models.Model):
    """Model representing a chat room. Chat rooms have a short, human-readable
    name, a slug that is their URI, and a topic."""

    id = models.SlugField(primary_key=True)
    topic = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('id',)

    def __iter__(self):
        return {
            'slug': self.id,
            'topic': self.topic,
        }.iteritems()

    @property
    def redis_key(self):
        return 'room_%s' % self.id


class Event(models.Model):
    """Model representing a single event occurring within a chat room."""

    room = models.ForeignKey(Room)
    user_name = models.CharField(max_length=30, db_index=True)
    event_type = models.CharField(max_length=20, choices=(
        ('statement', 'Statement'),
        ('user_joined', 'User Joined'),
        ('user_left', 'User Left'),
        ('topic_set', 'Topic Set'),
    ), db_index=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)

    def __iter__(self):
        # Most of the time, just send down a rough dictionary representation
        # of the object.
        answer = {
            'room': self.room.id,
            'type': self.event_type,
            'user': self.user_name,
            'message': self.message,
            'timestamp': self.created.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Edge Case: On topics, I would prefer send down a more descriptive
        # message, as well as an extra `topic` key with just the new topic.
        if self.event_type == 'topic_set':
            answer['topic'] = self.message
            answer['message'] = '{user} set the topic to "{topic}".'.format(
                topic=self.message,
                user=self.user_name,
            )

        # Okay, done.
        return answer.iteritems()

    def save(self, *args, **kwargs):
        """Save the event, and publish the event in Redis."""

        # If this is a user_joined or user_left event,
        # set a consistent message.
        if self.event_type == 'user_joined':
            self.message = '%s has joined the room.' % self.user_name
        if self.event_type == 'user_left':
            self.message = '%s has left the room.' % self.user_name

        # Perform a standard save.
        return_value = super(Event, self).save(*args, **kwargs)

        # Create a Redis object.
        redis = Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB),
            password=settings.REDIS_PASSWORD,
        )

        # Publish the event in Redis.
        redis.publish(self.room.redis_key, json.dumps(dict(self)))
        return return_value