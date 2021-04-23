from rest_framework import generics, serializers
from regcore.models import Part


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = "__all__"


class ListPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        exclude = ["document",]


class PartsView(generics.ListCreateAPIView):
    serializer_class = ListPartSerializer

    def get_queryset(self):
        return Part.objects.all()

class EffectiveTitlesView(generics.ListAPIView):
    serializer_class = ListPartSerializer

    def get_queryset(self):
        date = self.kwargs.get("date")
        return Part.objects.filter(date__lte=date).order_by("name", "-date").distinct("name")

class EffectivePartsView(generics.ListAPIView):
    serializer_class = ListPartSerializer

    def get_queryset(self):
        title = self.kwargs.get("title")
        date = self.kwargs.get("date")
        return Part.objects.filter(date__lte=date).order_by("name", "-date").distinct("name")

class PartView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PartSerializer
    lookup_field = "name"

    def get_queryset(self):
        title = self.kwargs.get("title")
        date = self.kwargs.get("date")
        return Part.objects.filter(date=date).filter(title=title)

# class PartView(views.RetrieveModelMixin, views.UpdateModelMixin, views.DeleteModelMixin, views.views.GenericAPIView):
    
#     serializer_class = PartSerializer

#     def get_queryset(self):
#         date = self.kwargs.get("date")
#         title = self.kwargs.get("title")
#         part = self.kwargs.get("part")
#         return Part.objects.filter(date=date, title=title, part=part)