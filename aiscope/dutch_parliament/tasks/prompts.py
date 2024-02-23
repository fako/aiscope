from typing import List

from django.db.transaction import atomic
from celery import current_app as app

from datagrowth.utils.tasks import DatabaseConnectionResetTask
from datagrowth.datatypes import DataStorages
from datagrowth.processors import HttpGrowthProcessor


@app.task(name="dutch_parliament.get_b1_motion", base=DatabaseConnectionResetTask)
@atomic()
def get_b1_motion(label: str, document_ids: List[int]):
    storages = DataStorages.from_label(label)
    http_processor = HttpGrowthProcessor({
        "datatypes_app_label": storages.app_label,
        "growth_phase": "dutch_parliament.get_b1_motion",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "to_property": "b1_motion",
        "retrieve_data": {
            "resource": "core.openaipromptresource",
            "method": "post",
            "args": ["b1-language-level.tpl"],
            "kwargs": {"text": "$.motion"},
        },
        "extractor": "ExtractProcessor.pass_resource_through",
        "contribute_data": {}
    })
    http_processor(storages.Document.objects.filter(id__in=document_ids))
