from django.shortcuts import render
from django.http import HttpResponse

# from ldm.dream.artQuery import ArtQuery, schema
from ldm.dream.pngwriter import PngWriter
from threading import Event

def index(request):
    return HttpResponse("Hello, world. You're at the paintingMuse index.")

def old(request):
   return render(request, "./static/index.html") 