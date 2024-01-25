from datetime import datetime

from django.utils.timezone import make_aware
from django.contrib.contenttypes.fields import GenericRelation

from datagrowth.datatypes import DatasetBase
from datagrowth.datatypes.datasets.constants import GrowthStrategy

from political_discourse.models.datasets.dutch_parliament.objectives import (
    VOTE_RECORDS_OBJECTIVE,
    MOTION_VOTES_OBJECTIVE,
    MOTION_CONTENT_OBJECTIVE
)


class DutchParliamentMotionsDataset(DatasetBase):

    versions = GenericRelation(
        "MotionDatasetVersion",
        content_type_field="dataset_type",
        object_id_field="dataset_id",
        related_query_name="datasets"
    )

    GROWTH_STRATEGY = GrowthStrategy.STACK

    DATASET_VERSION_MODEL = "MotionDatasetVersion"
    COLLECTION_IDENTIFIER = "motion_id"
    SEEDING_PHASES = [
        {
            "phase": "vote_records",
            "strategy": "initial",
            "batch_size": 5,
            "retrieve_data": {
                "resource": "political_discourse.DutchParlementRecordSearch",
                "method": "get",
                "args": [],
                "kwargs": {},
                "continuation_limit": 9999,
                "$start_date": make_aware(datetime(year=2006, month=1, day=1)).strftime("%Y-%m-%d"),  # start Rutte era
                "$end_date": None  # will go up to end of last year
            },
            "contribute_data": {
                "objective": VOTE_RECORDS_OBJECTIVE
            }
        },
        {
            "phase": "motion_votes",
            "strategy": "merge",
            "batch_size": 5,
            "retrieve_data": {
                "resource": "political_discourse.DutchParlementRecord",
                "method": "get",
                "args": ["$.url"],  # will be the sitting url
                "kwargs": {},
            },
            "contribute_data": {
                "objective": MOTION_VOTES_OBJECTIVE,
                "merge_base": "buffer",
                "merge_on": "vote_record_id",
                "composition_to": "sitting"
            }
        },
        {
            "phase": "motion_content",
            "strategy": "merge",
            "batch_size": 5,
            "retrieve_data": {
                "resource": "political_discourse.DutchParlementRecord",
                "method": "get",
                "args": ["$.url"],  # will be the motion url
                "kwargs": {},
            },
            "contribute_data": {
                "objective": MOTION_CONTENT_OBJECTIVE,
            }
        },
    ]

    def get_signature_from_input(self, *args, **kwargs):
        """
        We'll exclude $start_date and $end_date from the signature,
        because we want to stack Collections by year in the same Dataset.
        Instead of creating a new Dataset everytime we run growth for a new year.
        """
        kwargs.pop("$start_date", None)
        kwargs.pop("$end_date", None)
        return super().get_signature_from_input(*args, **kwargs)