import os
import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.template.loader import get_template

from datagrowth.resources.testing import ResourceFixturesMixin

from core.openai.resources.prompts import OpenaiPromptResource


class TestOpenAIEmbeddingsResource(ResourceFixturesMixin, TestCase):

    resource_fixtures = ["prompts"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        motion_fixture_file_path = os.path.join(
            settings.BASE_DIR, "dutch_parliament", "fixtures", "samples", "motion_text.txt"
        )
        with open(motion_fixture_file_path) as motion_file:
            cls.motion_text = motion_file.read()

    @staticmethod
    def get_prompt_render(template_name, context):
        template = get_template(template_name)
        render = template.render(context=context)
        return render

    @staticmethod
    def patch_finish_reason(resource, reason):
        json_body = json.loads(resource.body)
        for choice in json_body["choices"]:
            choice["finish_reason"] = reason
        resource.body = json.dumps(json_body)

    def assert_prompt_request(self, request, template, text, extra_request_data=None):
        self.assertIsInstance(request, dict)
        self.assertEqual(request["args"], (template,))
        self.assertEqual(request["kwargs"], {"text": text})
        self.assertEqual(request["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        render = self.get_prompt_render(template, {"text": text})
        expected_request_data = {
            "model": "gpt-3.5-turbo-0125",
            "messages": [
                {
                    "role": "user",
                    "content": render
                }
            ]
        }
        if extra_request_data:
            expected_request_data.update(extra_request_data)
        if template.endswith(".json.tpl"):
            expected_request_data["response_format"] = {"type": "json_object"}
        self.assertEqual(request["json"], expected_request_data)
        self.assertTrue(request["token_count"])

    def assert_canceled_request(self, request, template, text):
        self.assertIsInstance(request, dict)
        self.assertEqual(request["args"], (template,))
        self.assertEqual(request["kwargs"], {"text": text})
        self.assertEqual(request["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        self.assertTrue(request["cancel"])
        self.assertEqual(request["json"], {})
        self.assertIsNone(request["token_count"])

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_plain(self, send_mock):
        prompt = "b1-language-level.tpl"
        rsc = OpenaiPromptResource()
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 1)
        self.assert_prompt_request(rsc.request, prompt, self.motion_text)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_json(self, send_mock):
        prompt = "topic-and-title.json.tpl"
        rsc = OpenaiPromptResource()
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 1)
        self.assert_prompt_request(rsc.request, prompt, self.motion_text)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_custom_option(self, send_mock):
        prompt = "topic-and-title.json.tpl"
        config = {
            "options": {"n": 3}
        }
        rsc = OpenaiPromptResource(config=config)
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 1)
        extra_request_data = {"n": 3}
        self.assert_prompt_request(rsc.request, prompt, self.motion_text, extra_request_data=extra_request_data)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_exceed_max_tokens(self, send_mock):
        prompt = "topic-and-title.json.tpl"
        rsc = OpenaiPromptResource()
        with patch.object(OpenaiPromptResource, "MODEL_MAX_TOKENS", 100):
            rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(rsc.status, rsc.ErrorCodes.MAX_TOKENS_EXCEEDED.value)
        self.assert_canceled_request(rsc.request, prompt, self.motion_text)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_invalid_template_input(self, send_mock):
        prompt = "does-not-exist.json.tpl"
        rsc = OpenaiPromptResource()
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(rsc.status, rsc.ErrorCodes.TEMPLATE_DOES_NOT_EXIST.value)
        self.assert_canceled_request(rsc.request, prompt, self.motion_text)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_template_does_not_exist(self, send_mock):
        prompt = "does-not-exist.json.tpl"
        rsc = OpenaiPromptResource()
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(rsc.status, rsc.ErrorCodes.TEMPLATE_DOES_NOT_EXIST.value)
        self.assert_canceled_request(rsc.request, prompt, self.motion_text)

    @patch("core.openai.resources.prompts.HttpResource._send")
    def test_post_template_syntax_error(self, send_mock):
        prompt = "syntax-error.tpl"
        rsc = OpenaiPromptResource()
        rsc.post(prompt, text=self.motion_text)

        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(rsc.status, rsc.ErrorCodes.TEMPLATE_SYNTAX_ERROR.value)
        self.assert_canceled_request(rsc.request, prompt, self.motion_text)

    def test_finish_reason_length(self):
        rsc = OpenaiPromptResource.objects.get(id=1)
        self.patch_finish_reason(rsc, "length")
        rsc.handle_errors()

        self.assertFalse(rsc.success)
        self.assertEqual(rsc.status, rsc.ErrorCodes.MAX_TOKENS_EXCEEDED.value)

    def test_finish_reason_content_filter(self):
        rsc = OpenaiPromptResource.objects.get(id=1)
        self.patch_finish_reason(rsc, "content_filter")
        rsc.handle_errors()

        self.assertFalse(rsc.success)
        self.assertEqual(rsc.status, rsc.ErrorCodes.CONTENT_FILTER.value)

    def test_content_plain(self):
        rsc = OpenaiPromptResource.objects.get(id=1)
        content_type, data = rsc.content

        self.assertEqual(content_type, "text/plain")
        self.assertIsInstance(data, str)
        self.assertTrue(data.startswith("Er zijn gegevens verzameld over de Nederlandse moslimgemeenschap"))

    def test_content_json(self):
        rsc = OpenaiPromptResource.objects.get(id=2)
        content_type, data = rsc.content

        self.assertEqual(content_type, "application/json")
        self.assertIsInstance(data, dict)
        self.assertEqual(
            sorted(list(data.keys())), ["title", "topic"],
            "Expected hashed texts as keys for content output"
        )
        self.assertEqual(data["title"], "Onrechtmatige verzameling van persoonsgegevens Nederlandse moslims")
        self.assertEqual(data["topic"], "Privacy van moslimgemeenschap in Nederland")

    def test_empty_content(self):
        rsc = OpenaiPromptResource()
        content_type, data = rsc.content
        
        self.assertIsNone(content_type)
        self.assertIsNone(data)
