from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings

import uuid

class PaintingMutation(models.Model):
    prompt = models.CharField(max_length=600)
    request_date = models.DateTimeField('date published')

    def __str__(self):
        return self.prompt

class Painting(models.Model):
    prompt = models.TextField
    name = models.CharField(max_length=280)
    created_at = models.DateTimeField('date published')
    image_url = models.URLField(max_length=1000)
    mutation = models.ForeignKey(PaintingMutation, on_delete=models.CASCADE)
    artist_id = models.CharField(max_length=2)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        default=1,
    )

    def __str__(self):
        return self.name

# class Player(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     def __str__(self):
#         return self.name