from typing import List

from django.db.transaction import atomic
from celery import current_app as app

from datagrowth.utils.tasks import DatabaseConnectionResetTask
from datagrowth.datatypes import DataStorages


@app.task(name="dutch_parliament.get_claim_texts", base=DatabaseConnectionResetTask)
@atomic()
def get_claim_texts(label: str, document_ids: List[int]):
    storages = DataStorages.from_label(label)
    for document in storages.Document.objects.filter(id__in=document_ids).select_for_update():
        texts = document.get_claim_texts()
        document.derivatives["dutch_parliament.get_claim_texts"] = {"texts": texts}
        document.task_results["dutch_parliament.get_claim_texts"] = {"success": bool(texts)}
        document.save()
