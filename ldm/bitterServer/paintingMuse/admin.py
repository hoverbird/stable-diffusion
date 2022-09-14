from django.contrib import admin

# Register your models here.
from models import Painting, PaintingMutation, Player

admin.site.register(Painting)
admin.site.register(PaintingMutation)
