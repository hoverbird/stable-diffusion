import graphene

from graphene_django import DjangoObjectType, DjangoListField 
from .models import Painting#, PaintingMutation 


class PaintingType(DjangoObjectType): 
    class Meta:
        model = Painting
        fields = "__all__"

class PaintingInput(graphene.InputObjectType):
    id = graphene.ID()
    title = graphene.String(default_value="Untitled")
    artist_id = graphene.String()
    prompt = graphene.String() 

class Query(graphene.ObjectType):
    all_paintings = graphene.List(PaintingType)
    painting = graphene.Field(PaintingType, painting_id=graphene.Int())

    def resolve_all_paintings(self, info, **kwargs):
        return Painting.objects.all()

    def resolve_painting(self, info, painting_id):
        return Painting.objects.get(pk=painting_id)



class CreatePainting(graphene.Mutation):
    class Arguments:
        painting_data = PaintingInput(required=True)

    painting = graphene.Field(PaintingType)

    @staticmethod
    def mutate(root, info, painting_data=None):
        painting_instance = Painting(
            prompt=painting_data.prompt,
            title=painting_data.title,
            artist_id=painting_data.artist_id,
        )
        painting_instance.save()
        return CreatePainting(painting=painting_instance)


class UpdatePainting(graphene.Mutation):
    class Arguments:
        # The input arguments for this mutation
        title = graphene.String(required=True)
        id = graphene.ID()

    # The class attributes define the response of the mutation
    painting = graphene.Field(PaintingType)

    @classmethod
    def mutate(cls, root, info, title, id):
        painting = Painting.objects.get(pk=id)
        painting.title = title
        painting.save()
        # Notice we return an instance of this mutation
        return UpdatePainting(painting=painting)


class Mutation(graphene.ObjectType):
    create_painting = CreatePainting.Field()
    update_painting = UpdatePainting.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
