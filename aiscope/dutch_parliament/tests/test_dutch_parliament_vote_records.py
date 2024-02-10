from django.test import TestCase

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor
from datagrowth.resources.testing import ResourceFixturesMixin

from dutch_parliament.models import DutchParlementRecordSearch, DutchParlementRecord
from dutch_parliament.objectives import VOTE_RECORDS_OBJECTIVE, MOTION_VOTES_OBJECTIVE, MOTION_CONTENT_OBJECTIVE


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


class TestMotionRecordsExtraction(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["dutch-parliament"]

    def test_government_request(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_CONTENT_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/kst-19637-1020.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(content[0], {
            "motion_id": "kst-19637-1020",
            "action": {
                "type": "request",
                "audience": "de regering",
                "text": "in het nieuwe ambtsbericht over de democratische republiek congo alle beschikbare "
                        "betrouwbare bronnen te betrekken en tot uitdrukking te brengen",
                "points": []
            },
            "premises": [
                (
                    "consideration",
                    "het kabinet in navolging van de commissie-havermans van oordeel is, "
                    "dat de congolese autoriteiten van elke door nederland uitgezette congolees aannemen, "
                    "dat deze asiel heeft gevraagd, tenzij het tegendeel blijkt",
                ),
                (
                    "consideration",
                    "het ambtsbericht van het ministerie van buitenlandse zaken over de democratische republiek congo "
                    "van september 2005 slechts beperkt informatie verschaft over de geraadpleegde bronnen "
                    "met betrekking tot het karakter van de direction g\u00e9n\u00e9rale de migration en "
                    "de risico\u2019s bij terugkeer als bekend is dat iemand asiel heeft gevraagd",
                ),
                (
                    "consideration",
                    "diverse bronnen, waaronder het ambtsbericht van het verenigd koninkrijk, "
                    "terzake van deze onderwerpen andere informatie bevatten dan het nederlandse ambtsbericht",
                ),
                (
                    "consideration",
                    "deze bronnen deels van recentere datum en daardoor actueler zijn dan het ambtsbericht",
                ),
                (
                    "consideration",
                    "daardoor een alomvattend beeld ontbreekt over de mogelijke risico\u2019s die uitgezette congolese "
                    "ex-asielzoekers momenteel bij aankomst te kinshasa lopen",
                ),
                (
                    "consideration",
                    "de unhcr ervoor waarschuwt dat congolese staatsburgers met een militaire of "
                    "politieke achtergrond bij terugkeer naar congo extra gevaar lopen, "
                    "indien bekend is dat zij asiel hebben gevraagd",
                )
            ]
        })

    def test_institute_request(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_CONTENT_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/kst-32824-405.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(content[0], {
            "motion_id": "kst-32824-405",
            "action": {
                "type": "suggestion",
                "audience": "de autoriteit persoonsgegevens",
                "text": "onderzoek te doen naar de volgende aspecten",
                "points": [
                    "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld",
                    "met welke actoren deze informatie vervolgens is gedeeld",
                    "wat er met deze persoonsgegevens is gedaan, of het is gebruikt voor besluiten en "
                    "of er mogelijk gevolgen zijn geweest voor Nederlandse moslims door de registratie van "
                    "hun persoonsgegevens"
                ]
            },
            "premises": [
                (
                    "observation",
                    "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag",
                ),
                (
                    "consideration",
                    "dit is gedaan door onderdelen van de nederlandse overheid, waar verschillende ministeries en "
                    "organisaties deel van uitmaken, zoals de taskforce problematisch gedrag, "
                    "zodat persoonsgegevens op meerdere plekken zouden kunnen zijn opgeslagen",
                ),
                (
                    "consideration",
                    "persoonsgegevens ook zijn gedeeld met gemeenten, de politie, ministeries en veiligheidspartners "
                    "door de leden van de taskforce problematisch gedrag",
                ),
                (
                    "opinion",
                    "voorkomen dient te worden dat persoonsgegevens van nederlandse moslims nog ergens rondslingeren "
                    "of dat de gegevens nog worden gebruikt",
                )
            ]
        })

    def test_variance_government_request(self):
        # Setup extraction
        config = create_config("global", {
            "objective": MOTION_CONTENT_OBJECTIVE
        })
        extractor = ExtractProcessor(config=config)
        resource = DutchParlementRecord.objects.get(uri="zoek.officielebekendmakingen.nl/kst-32824-399.html")
        # Extract content and assert
        content = list(extractor.extract_from_resource(resource))
        self.assertEqual(content[0], {
            "motion_id": "kst-32824-399",
            "action": {
                "type": "request",
                "audience": "de regering",
                "text": "alle mensen waarbij het herleidbaar is dat ze onwettig zijn geregistreerd "
                        "een persoonlijke excuusbrief te sturen namens de regering",
                "points": []
            },
            "premises": [
                (
                    "observation",
                    "er zonder wettelijke grondslag gegevens zijn verzameld over de nederlandse moslimgemeenschap"
                ),
                (
                    "consideration",
                    "bij de afhandeling van de fsv-registraties mensen een persoonlijke excuusbrief hebben gekregen"
                )
            ]
        })
