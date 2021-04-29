from rest_framework import generics, serializers
from django.db import models

from regcore.models import Part

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = "__all__"


class ListPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = "__all__"
        extra_kwargs = {
            'document': {'write_only': True}
        }


class ListEffectivePartSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document__title", read_only=True)

    class Meta:
        model = Part
        fields = ("name", "title", "date", "last_updated", "structure", "document_title")


class PartsView(generics.ListCreateAPIView):
    serializer_class = ListPartSerializer

    def get_queryset(self):
        return Part.objects.all()
    
    def create(self, request, *args, **kwargs):
        query = Part.objects.filter(
            name=request.data.get("name"),
            title=request.data.get("title"),
            date=request.data.get("date"),
        )
        if query.exists():
            serializer = self.get_serializer(query.get(), data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        return super().create(request, *args, **kwargs)


class EffectiveTitlesView(generics.ListAPIView):
    serializer_class = ListEffectivePartSerializer

    def get_queryset(self):
        date = self.kwargs.get("date")
        return Part.objects.filter(date__lte=date).order_by("name", "-date").distinct("name").values("name", "title", "date", "last_updated", "structure", "document__title")

class EffectivePartsView(generics.ListAPIView):
    serializer_class = ListEffectivePartSerializer

    def get_queryset(self):
        title = self.kwargs.get("title")
        date = self.kwargs.get("date")
        return Part.objects.filter(title=title).filter(date__lte=date).order_by("name", "-date").distinct("name")


class EffectivePartView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PartSerializer
    lookup_field = "name"

    def get_queryset(self):
        title = self.kwargs.get("title")
        date = self.kwargs.get("date")
        return Part.objects.filter(title=title).filter(date__lte=date)
    
    def get_object(self):
        return self.get_queryset().filter(name=self.kwargs.get(self.lookup_field)).latest("date")
