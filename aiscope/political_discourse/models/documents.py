from datagrowth.datatypes import DatasetVersionBase, CollectionBase, DocumentBase


class DatasetVersion(DatasetVersionBase):
    pass


class Collection(CollectionBase):

    @property
    def documents(self):
        return self.document_set


class Document(DocumentBase):
    pass
