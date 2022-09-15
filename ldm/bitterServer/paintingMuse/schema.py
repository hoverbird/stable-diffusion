import graphene

from graphene_django import DjangoObjectType, DjangoListField 
from .models import Painting, PaintingMutation 


class PaintingType(DjangoObjectType): 
    class Meta:
        model = Painting
        fields = "__all__"


class Query(graphene.ObjectType):
    all_paintings = graphene.List(PaintingType)
    painting = graphene.Field(PaintingType, painting_id=graphene.Int())

    def resolve_all_paintings(self, info, **kwargs):
        return Painting.objects.all()

    def resolve_painting(self, info, painting_id):
        return Painting.objects.get(pk=painting_id)

schema = graphene.Schema(query=Query) #, mutation=Mutation)
