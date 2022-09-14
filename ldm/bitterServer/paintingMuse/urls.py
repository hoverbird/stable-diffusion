from django.urls import path
from django.contrib import admin
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("admin/", admin.site.urls),
    path('old', views.old, name='old'),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
