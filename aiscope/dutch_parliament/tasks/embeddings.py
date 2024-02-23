from typing import List

from django.db.transaction import atomic
from celery import current_app as app

from datagrowth.utils.tasks import DatabaseConnectionResetTask
from datagrowth.datatypes import DataStorages

from core.openai.processors.growth.embeddings import EmbeddingsGrowthProcessor


@app.task(name="dutch_parliament.get_claim_embeddings", base=DatabaseConnectionResetTask)
@atomic()
def get_claim_embeddings(label: str, document_ids: List[int]):
    storages = DataStorages.from_label(label)
    embeddings_processor = EmbeddingsGrowthProcessor({
        "datatypes_app_label": storages.app_label,
        "growth_phase": "dutch_parliament.get_claim_embeddings",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "core.openaiembeddingsresource",
            "method": "post",
            "args": ["$.claims"],
            "kwargs": {},
        },
        "extractor": "ExtractProcessor.pass_resource_through",
        "contribute_data": {}
    })
    embeddings_processor(storages.Document.objects.filter(id__in=document_ids))
