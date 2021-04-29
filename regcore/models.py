from django.db import models

from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from mptt.querysets import TreeQuerySet

from regcore.fields import CompressedJSONField


class Part(models.Model):
    name = models.CharField(max_length=8)
    title = models.CharField(max_length=8)
    date = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)
    document = models.JSONField()
    structure = models.JSONField()

    class Meta:
        unique_together = ['name', 'title', 'date']


class DocumentQuerySet(TreeQuerySet):
    def only_latest(self):
        notice = Notice.objects.filter(document_number=models.OuterRef('version'))
        notice = notice.order_by('-effective_on')
        q = self.annotate(effective_on=models.Subquery(notice.values('effective_on')[:1]))
        q = q.order_by('label_string', '-effective_on')
        q = q.distinct('label_string')
        return q


class DocumentManager(TreeManager):

    def get_queryset(self, *args, **kwargs):
        return DocumentQuerySet(self.model, using=self._db).order_by(self.tree_id_attr, self.left_attr)

    def only_latest(self):
        notice = Notice.objects.filter(document_number=models.OuterRef('version'))
        notice = notice.order_by('-effective_on')
        sections_query = self.annotate(effective_on=models.Subquery(notice.values('effective_on')[:1]))
        sections_query = sections_query.order_by('label_string', '-effective_on')
        sections_query = sections_query.distinct('label_string')
        return self.filter(id__in=models.Subquery(sections_query.values('id')))\
            .annotate(effective_on=models.Subquery(notice.values('effective_on')[:1]))


class Document(MPTTModel):
    id = models.TextField(primary_key=True)     # noqa
    doc_type = models.SlugField(max_length=20)
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True, on_delete=models.CASCADE)
    version = models.SlugField(max_length=20, null=True, blank=True)
    label_string = models.SlugField(max_length=200)
    text = models.TextField()
    title = models.TextField(blank=True)
    node_type = models.SlugField(max_length=30)
    root = models.BooleanField(default=False, db_index=True)

    objects = DocumentManager()

    class Meta:
        index_together = (('doc_type', 'version', 'label_string'),)
        unique_together = (('doc_type', 'version', 'label_string'),)


class Layer(models.Model):
    name = models.SlugField(max_length=20)
    layer = CompressedJSONField()
    doc_type = models.SlugField(max_length=20)
    # We allow doc_ids to contain slashes, which are particularly important
    # for CFR docs, which use the [version_id]/[reg_label_id] format. It might
    # make sense to split off a version identifier into a separate field in
    # the future, if we can't treat that doc_id as an opaque string
    doc_id = models.SlugField(max_length=250)

    class Meta:
        index_together = (('name', 'doc_type', 'doc_id'),)
        unique_together = index_together


class Notice(models.Model):
    document_number = models.SlugField(max_length=20, primary_key=True)
    effective_on = models.DateField(null=True)
    fr_url = models.CharField(max_length=200, null=True)
    publication_date = models.DateField()
    notice = CompressedJSONField()


class NoticeCFRPart(models.Model):
    """Represents the one-to-many relationship between notices and CFR parts"""
    cfr_part = models.SlugField(max_length=10, db_index=True)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)

    class Meta:
        index_together = (('notice', 'cfr_part'),)
        unique_together = (('notice', 'cfr_part'),)


class Diff(models.Model):
    label = models.SlugField(max_length=200)
    old_version = models.SlugField(max_length=20)
    new_version = models.SlugField(max_length=20)
    diff = CompressedJSONField()

    class Meta:
        index_together = (('label', 'old_version', 'new_version'),)
        unique_together = (('label', 'old_version', 'new_version'),)
