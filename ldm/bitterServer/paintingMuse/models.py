from asyncio.windows_events import NULL
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings
import django.utils.timezone
import pytz
from datetime import datetime

import uuid

# class PaintingMutation(models.Model):
#     prompt = models.CharField(max_length=600)
#     request_date = models.DateTimeField('date published')

#     def __str__(self):
#         return self.prompt


# Fields to add:
# parent image]
# seed

class Painting(models.Model):
    title = models.CharField(max_length=280, default="Untitled")
    created_at = models.DateTimeField('date published', default=datetime.now(pytz.utc))
    inspiration_image_url = models.URLField(max_length=1000, blank=True, null=True)
    # mutation = models.ForeignKey(PaintingMutation, on_delete=models.CASCADE)
    artist_id = models.CharField(max_length=12, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="Player who created the painting."
    )
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    prompt = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title

# class Player(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     def __str__(self):
#         return self.name