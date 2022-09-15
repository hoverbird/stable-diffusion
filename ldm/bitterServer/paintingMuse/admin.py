from django.contrib import admin

# # Register your models here.
from .models import Painting#, PaintingMutation
# # import models.Painting

admin.site.register(Painting)
# admin.site.register(PaintingMutation)
