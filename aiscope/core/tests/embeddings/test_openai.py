from unittest.mock import patch

from django.test import TestCase

from datagrowth.resources.testing import ResourceFixturesMixin

from core.openai.resources.embeddings import OpenaiEmbeddingsResource


class TestOpenAIEmbeddingsResource(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["embeddings"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.prepared_test_motion = {
            "3834e95ca98a5d7ebf6fc21dfcb24c878ce1efc4":
                "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld",
            "3b7fbbe07c209a45dd9c408edb0f2671de530c54":
                "met welke actoren deze informatie vervolgens is gedeeld",
            "42963196ba7f699b642bf8575ceb4b7ee7c49f0e":
                "wat er met deze persoonsgegevens is gedaan, of het is gebruikt voor besluiten en "
                "of er mogelijk gevolgen zijn geweest voor Nederlandse moslims door "
                "de registratie van hun persoonsgegevens",
            "7092ef9e230d30f6934509b281d426fd6dfceefe":
                "voorkomen dient te worden dat persoonsgegevens van nederlandse moslims nog ergens rondslingeren of "
                "dat de gegevens nog worden gebruikt",
            "82815ed3055b7725134631454d26008eb10c2fa9":
                "persoonsgegevens ook zijn gedeeld met gemeenten, de politie, ministeries en veiligheidspartners door "
                "de leden van de taskforce problematisch gedrag",
            "984593ef9f11fa9989bf6bba8c495701a774071e":
                "dit is gedaan door onderdelen van de nederlandse overheid, "
                "waar verschillende ministeries en organisaties deel van uitmaken, "
                "zoals de taskforce problematisch gedrag, "
                "zodat persoonsgegevens op meerdere plekken zouden kunnen zijn opgeslagen",
            "e7c1023668ea4f7fa15259e58caf34defe2faca2":
                "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag"
        }

    def assert_embeddings_request(self, request, payloads, payload_index):
        self.assertIsInstance(request, dict)
        self.assertEqual(request["args"], (self.prepared_test_motion,))
        self.assertEqual(request["kwargs"], {})
        self.assertEqual(request["url"], "https://api.openai.com/v1/embeddings")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        self.assertEqual(request["payloads"], payloads)
        self.assertEqual(request["payload_index"], payload_index)
        expected_payload = payloads[payload_index]
        expected_texts = OpenaiEmbeddingsResource.text_payload_to_data(expected_payload)
        self.assertEqual(request["json"], {
            "model": "text-embedding-ada-002",
            "encoding_format": "float",
            "input": expected_texts

        })

    def test_text_payload_to_data(self):
        texts = OpenaiEmbeddingsResource.text_payload_to_data([
            [
                "e7c1023668ea4f7fa15259e58caf34defe2faca2",
                "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag"
            ],
            [
                "3834e95ca98a5d7ebf6fc21dfcb24c878ce1efc4",
                "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld"
            ],
            [
                "3b7fbbe07c209a45dd9c408edb0f2671de530c54",
                "met welke actoren deze informatie vervolgens is gedeeld"
            ]
        ])
        self.assertEqual(texts, [
            "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag",
            "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld",
            "met welke actoren deze informatie vervolgens is gedeeld"
        ])

    def test_prepare_text_fragments(self):
        texts = OpenaiEmbeddingsResource.prepare_text_fragments([
            "this is a test",
            "with two texts"
        ])
        self.assertEqual(texts, {
            "fa26be19de6bff93f70bc2308434e4a440bbad02": "this is a test",
            "9b13c63b7b094aaa70f5010b3426015975835e43": "with two texts"
        })

    @patch("core.openai.resources.embeddings.HttpResource._send")
    def test_post(self, send_mock):
        rsc = OpenaiEmbeddingsResource()
        rsc.post(self.prepared_test_motion)

        self.assertEqual(send_mock.call_count, 1)
        expected_payloads = [
            [
                [
                    "984593ef9f11fa9989bf6bba8c495701a774071e",
                    "dit is gedaan door onderdelen van de nederlandse overheid, "
                    "waar verschillende ministeries en organisaties deel van uitmaken, "
                    "zoals de taskforce problematisch gedrag, "
                    "zodat persoonsgegevens op meerdere plekken zouden kunnen zijn opgeslagen"
                ],
                [
                    "42963196ba7f699b642bf8575ceb4b7ee7c49f0e",
                    "wat er met deze persoonsgegevens is gedaan, "
                    "of het is gebruikt voor besluiten en of er mogelijk gevolgen zijn geweest voor "
                    "Nederlandse moslims door de registratie van hun persoonsgegevens"
                ],
                [
                    "82815ed3055b7725134631454d26008eb10c2fa9",
                    "persoonsgegevens ook zijn gedeeld met gemeenten, de politie, ministeries en "
                    "veiligheidspartners door de leden van de taskforce problematisch gedrag"
                ],
                [
                    "7092ef9e230d30f6934509b281d426fd6dfceefe",
                    "voorkomen dient te worden dat persoonsgegevens van nederlandse moslims nog ergens "
                    "rondslingeren of dat de gegevens nog worden gebruikt"
                ],
                [
                    "e7c1023668ea4f7fa15259e58caf34defe2faca2",
                    "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag"
                ],
                [
                    "3834e95ca98a5d7ebf6fc21dfcb24c878ce1efc4",
                    "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld"
                ],
                [
                    "3b7fbbe07c209a45dd9c408edb0f2671de530c54",
                    "met welke actoren deze informatie vervolgens is gedeeld"
                ]
            ]
        ]
        self.assert_embeddings_request(rsc.request, expected_payloads, 0)

    @patch("core.openai.resources.embeddings.HttpResource._send")
    def test_post_exceed_max_tokens(self, send_mock):
        rsc = OpenaiEmbeddingsResource()
        with patch.object(OpenaiEmbeddingsResource, "MODEL_MAX_TOKENS", 100):
            rsc.post(self.prepared_test_motion)

        self.assertEqual(send_mock.call_count, 1)
        expected_payloads = [
            [
                [
                    "984593ef9f11fa9989bf6bba8c495701a774071e",
                    "dit is gedaan door onderdelen van de nederlandse overheid, "
                    "waar verschillende ministeries en organisaties deel van uitmaken, "
                    "zoals de taskforce problematisch gedrag, "
                    "zodat persoonsgegevens op meerdere plekken zouden kunnen zijn opgeslagen"
                ],
                [
                    "7092ef9e230d30f6934509b281d426fd6dfceefe",
                    "voorkomen dient te worden dat persoonsgegevens van nederlandse moslims nog ergens "
                    "rondslingeren of dat de gegevens nog worden gebruikt"
                ]
            ],
            [
                [
                    "42963196ba7f699b642bf8575ceb4b7ee7c49f0e",
                    "wat er met deze persoonsgegevens is gedaan, "
                    "of het is gebruikt voor besluiten en of er mogelijk gevolgen zijn geweest voor "
                    "Nederlandse moslims door de registratie van hun persoonsgegevens"
                ],
                [
                    "82815ed3055b7725134631454d26008eb10c2fa9",
                    "persoonsgegevens ook zijn gedeeld met gemeenten, de politie, ministeries en "
                    "veiligheidspartners door de leden van de taskforce problematisch gedrag"
                ]
            ],
            [
                [
                    "e7c1023668ea4f7fa15259e58caf34defe2faca2",
                    "er gegevens zijn verzameld over de nederlandse moslimgemeenschap zonder wettelijke grondslag"
                ],
                [
                    "3834e95ca98a5d7ebf6fc21dfcb24c878ce1efc4",
                    "door welke actoren persoonsgegevens van Nederlandse moslims zijn verzameld"
                ],
                [
                    "3b7fbbe07c209a45dd9c408edb0f2671de530c54",
                    "met welke actoren deze informatie vervolgens is gedeeld"
                ]
            ]
        ]
        self.assert_embeddings_request(rsc.request, expected_payloads, 0)

    def test_content(self):
        resource = OpenaiEmbeddingsResource.objects.get(id=1)
        content_type, data = resource.content
        self.assertEqual(content_type, "application/json")
        self.assertIsInstance(data, dict)
        self.assertEqual(sorted(list(data.keys())), [
            "9b13c63b7b094aaa70f5010b3426015975835e43",
            "fa26be19de6bff93f70bc2308434e4a440bbad02"
        ], "Expected hashed texts as keys for content output")
        for key, embeddings in data.items():
            self.assertIsInstance(embeddings, list)
            self.assertEqual(len(embeddings), 1536, "Expected content values to contain embeddings")

    def test_empty_content(self):
        resource = OpenaiEmbeddingsResource()
        content_type, data = resource.content
        self.assertIsNone(content_type)
        self.assertIsNone(data)
