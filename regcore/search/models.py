from django.db import models

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVector, SearchVectorField

from regcore.models import Part


class SearchIndex(models.Model):
    type = models.CharField(max_length=32)
    label = ArrayField(base_field=models.CharField(max_length=32))
    content = models.TextField()
    parent = models.JSONField(null=True)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    search_vector = SearchVectorField()

    class Meta:
        unique_together = ['label', 'part']


def create_search(part, piece, memo, parent=None, ):
    try:
        memo.append(SearchIndex(
            label = piece["label"],
            part = part,
            parent = parent,
            type = piece["node_type"],
            content = piece.get("text") or piece.get("title"),
        ))
    except KeyError:
        pass

    children = piece.pop("children", []) or []
    for child in children:
        create_search(part, child, memo, parent=piece)
    return memo


def update_search(sender, instance, created, **kwargs):
    SearchIndex.objects.filter(part=instance).delete()
    contexts = create_search(instance, instance.document, [])
    SearchIndex.objects.bulk_create(contexts, ignore_conflicts=True)
    SearchIndex.objects.filter(part=instance).update(search_vector=SearchVector('content'))
