from datetime import datetime

from django.utils.timezone import make_aware

from datagrowth.datatypes import DatasetBase
from datagrowth.datatypes.datasets.constants import GrowthStrategy
from datagrowth.processors import HttpSeedingProcessor, SeedingProcessorFactory

from dutch_parliament.objectives import VOTE_RECORDS_OBJECTIVE, MOTION_VOTES_OBJECTIVE, MOTION_CONTENT_OBJECTIVE


class MotionsDataset(DatasetBase):
    """
    Example growth command: ./manage.py grow_dataset dutch_parliament.MotionsDataset -a "Migratie en integratie"
        -c "start_date=2023-01-01&end_date=2023-12-31" --limit=3
    """

    GROWTH_STRATEGY = GrowthStrategy.STACK

    COLLECTION_IDENTIFIER = "motion_id"
    SEEDING_PHASES = [
        {
            "phase": "vote_records",
            "strategy": "initial",
            "batch_size": 5,
            "retrieve_data": {
                "resource": "dutch_parliament.DutchParlementRecordSearch",
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
                "resource": "dutch_parliament.DutchParlementRecord",
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
                "resource": "dutch_parliament.DutchParlementRecord",
                "method": "get",
                "args": ["$.url"],  # will be the motion url
                "kwargs": {},
            },
            "contribute_data": {
                "objective": MOTION_CONTENT_OBJECTIVE,
            }
        },
    ]
    DOCUMENT_TASKS = {
        "dutch_parliament.get_motion_texts": {
            "depends_on": ["$.action", "$.premises"],
            "resources": [],
            "checks": []
        },
        "dutch_parliament.get_claim_embeddings": {
            "depends_on": ["dutch_parliament.get_motion_texts"],
            "resources": ["core.openaiembeddingsresource"],
            "checks": ["has_motion_texts"]
        },
        "dutch_parliament.get_b1_motion": {
            "depends_on": ["dutch_parliament.get_motion_texts"],
            "resources": ["core.openaipromptresource"],
            "checks": ["has_motion_texts"]
        }
    }

    def get_signature_from_input(self, *args, **kwargs):
        """
        We'll exclude $start_date and $end_date from the signature,
        because we want to stack Collections by year in the same Dataset.
        Instead of creating a new Dataset everytime we run growth for a new year.
        """
        kwargs.pop("$start_date", None)
        kwargs.pop("$end_date", None)
        return super().get_signature_from_input(*args, **kwargs)

    def get_seeding_factories(self):
        dataset_start_date = datetime.fromisoformat(self.config.start_date)
        dataset_end_date = datetime.fromisoformat(self.config.end_date)
        seeding_factories = {}
        for year in range(dataset_start_date.year, dataset_end_date.year+1):
            start_date = f"{year}-01-01" if year != dataset_start_date.year else \
                f"{year}-{dataset_start_date.month:02}-{dataset_start_date.day:02}"
            end_date = f"{year}-12-31" if year != dataset_end_date.year else \
                f"{year}-{dataset_end_date.month:02}-{dataset_end_date.day:02}"
            collection_name = f"end_date={end_date}&start_date={start_date}"
            seeding_factories[collection_name] = SeedingProcessorFactory(HttpSeedingProcessor, self.SEEDING_PHASES, {
                "start_date": start_date,
                "end_date": end_date
            })
        return seeding_factories
