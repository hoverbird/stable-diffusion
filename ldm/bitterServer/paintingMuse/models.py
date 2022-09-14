from django.db import models
from django.contrib.auth import get_user_model
import uuid

class PaintingMutation(models.Model):
    prompt = models.CharField(max_length=600)
    request_date = models.DateTimeField('date published')


class Painting(models.Model):
    prompt = models.TextField
    image_url = models.URLField
    mutation = models.ForeignKey(PaintingMutation, on_delete=models.CASCADE)
    artist_id = models.CharField(max_length=2)
    player = models.ForeignKey(Player)

class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
