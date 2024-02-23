from typing import List

from django.db.transaction import atomic
from celery import current_app as app

from datagrowth.utils.tasks import DatabaseConnectionResetTask
from datagrowth.datatypes import DataStorages


@app.task(name="dutch_parliament.get_motion_texts", base=DatabaseConnectionResetTask)
@atomic()
def get_motion_texts(label: str, document_ids: List[int]):
    storages = DataStorages.from_label(label)
    for document in storages.Document.objects.filter(id__in=document_ids).select_for_update():
        claim_texts = document.get_claim_texts()
        motion = document.get_motion_argument_text()
        document.derivatives["dutch_parliament.get_motion_texts"] = {
            "claims": claim_texts,
            "motion": motion
        }
        document.task_results["dutch_parliament.get_motion_texts"] = {
            "success": bool(claim_texts) and bool(motion)
        }
        document.save()
