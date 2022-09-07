from graphene import ObjectType, Field, ID, Schema, String

class ArtQuery(ObjectType):
    hello = String(prompt=String(default_value="A beautiful landscape."))

    def resolve_hello(root, info, prompt):
        print("**********************Hello Resolver")
        print(root)
        print(prompt)
        return prompt

schema = Schema(ArtQuery)