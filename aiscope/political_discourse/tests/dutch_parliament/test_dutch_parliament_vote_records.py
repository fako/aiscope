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
        self.assertEqual(len(content), 21)
        self.assertEqual(content[0], {
            "vote_record_id": "h-tk-20232024-13-19",
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
            "vote_record_id": "h-tk-20232024-13-19",
            "motion_id": "kst-32824-405",
            "url": "https://zoek.officielebekendmakingen.nl/kst-32824-405.html",
            "approvals": [
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
            "rejections": [
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
        self.assertEqual(content[0], {
            "vote_record_id": "h-tk-20052006-3563-3563",
            "motion_id": "kst-19637-1020",
            "url": "https://zoek.officielebekendmakingen.nl/kst-19637-1020.html",
            "approvals": [
                "SP",
                "GroenLinks",
                "PvdA",
                "ChristenUnie"
            ],
            "rejections": None,
            "outcome": "rejected"
        })

    def test_motion_votes_extraction_with_head_count(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_VOTES_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/h-tk-20232024-10-8.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(len(content), 31)
        head_vote = content[5]
        approvals = head_vote.pop("approvals")
        rejections = head_vote.pop("rejections")
        self.assertEqual(head_vote, {
            "vote_record_id": "h-tk-20232024-10-8",
            "motion_id": "kst-36333-44",
            "url": "https://zoek.officielebekendmakingen.nl/kst-36333-44.html",
            "outcome": "rejected"
        })
        self.assertEqual(len(approvals), 65)
        self.assertEqual(len(rejections), 82)
        self.assertEqual(approvals[:10], [
             "Tielen",
             "Valstar",
             "Verkuijlen",
             "Van Weerdenburg",
             "Van Wijngaarden",
             "Wilders",
             "Van der Woude",
             "Aartsen",
             "Agema",
             "Baudet",
        ])
        self.assertEqual(rejections[:10], [
            "Thijssen",
            "Vedder",
            "Wassenberg",
            "Werner",
            "Westerveld",
            "Van Weyenberg",
            "Wuite",
            "Akerboom",
            "Alkaya",
            "Amhaouch",
        ])
