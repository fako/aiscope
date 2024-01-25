from django.db import models

from datagrowth.datatypes import DatasetVersionBase, CollectionBase, DocumentBase


class MotionDatastorageMixin:
    DATASET_VERSION_MODEL = "MotionDatasetVersion"
    COLLECTION_MODEL = "MotionCollection"
    DOCUMENT_MODEL = "MotionDocument"


class MotionDatasetVersion(MotionDatastorageMixin, DatasetVersionBase):

    @property
    def collections(self):
        return self.motioncollection_set

    @property
    def documents(self):
        return self.motiondocument_set


class MotionCollection(MotionDatastorageMixin, CollectionBase):

    dataset_version = models.ForeignKey(MotionDatasetVersion, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def documents(self):
        return self.motiondocument_set


class MotionDocument(MotionDatastorageMixin, DocumentBase):

    dataset_version = models.ForeignKey(MotionDatasetVersion, null=True, blank=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(MotionCollection, blank=True, null=True, on_delete=models.CASCADE)
