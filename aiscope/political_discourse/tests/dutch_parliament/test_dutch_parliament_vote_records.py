from django.test import TestCase

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor
from datagrowth.resources.testing import ResourceFixturesMixin

from political_discourse.models import DutchParlementRecordSearch, DutchParlementRecord
from political_discourse.models.datasets.dutch_parliament.objectives import (
    VOTE_RECORDS_OBJECTIVE,
    MOTION_VOTES_OBJECTIVE
)


class TestVoteRecordsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["dutch-parliament"]

    def test_votes_search_extraction(self):
        # Setup extraction
        config = create_config("global", {
            "objective": VOTE_RECORDS_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecordSearch.objects.get(id=1)
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(len(content), 25)
        self.assertEqual(content[0], {
            "url": "https://zoek.officielebekendmakingen.nl/h-tk-20232024-13-19.html",
            "date": "2023-10-17",
            "parliamentary_session": "2023-2024",
            "sitting": "13-19",
            "political_body": "Tweede Kamer der Staten-Generaal"
        })

    def test_votes_search_next_request(self):
        first_page = DutchParlementRecordSearch.objects.get(id=1)
        next_request = first_page.create_next_request()
        self.assertIn(
            "pagina=2",
            next_request["url"],
            "Expected create_next_request to add pagina=2 to parameters to original request"
        )
        last_page = DutchParlementRecordSearch.objects.get(id=2)
        next_request = last_page.create_next_request()
        self.assertIsNone(next_request)

    def test_motion_votes_extraction(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_VOTES_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/h-tk-20232024-13-19.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0], {
            "url": "https://zoek.officielebekendmakingen.nl/kst-32824-405.html",
            "approve_factions": [
                "SP",
                "GroenLinks",
                "BIJ1",
                "Volt",
                "DENK",
                "PvdA",
                "PvdD",
                "D66",
                "Lid Omtzigt",
                "ChristenUnie",
                "SGP",
                "CDA"
            ],
            "reject_factions": [
                "Lid Ephraim",
                "VVD",
                "JA21",
                "Groep Van Haga",
                "PVV",
                "FVD",
                "BBB"
            ],
            "outcome": "approved"
        })

    def test_motion_votes_extraction_2006(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_VOTES_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/h-tk-20052006-3563-3563.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(len(content), 4)
        self.assertEqual(content[0],     {
            "url": "https://zoek.officielebekendmakingen.nl/kst-19637-1020.html",
            "approve_factions": [
                "SP",
                "GroenLinks",
                "PvdA",
                "ChristenUnie"
            ],
            "reject_factions": None,
            "outcome": "rejected"
        })
