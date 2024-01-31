from hashlib import sha1
import tiktoken
from operator import itemgetter

from django.core.exceptions import ValidationError

from datagrowth.resources.http import HttpResource


class OpenaiEmbeddingsResource(HttpResource):

    MODEL = "text-embedding-ada-002"
    MODEL_MAX_TOKENS = 8192

    URI_TEMPLATE = "https://api.openai.com/v1/embeddings"
    HEADERS = {
        "Content-Type": "application/json"
    }

    # TODO: next request based on token count: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.config.openai_api_key}"
        }

    def validate_input(self, method, *args, **kwargs):
        if method != "post":
            raise ValidationError("EmbeddingsResource only supports POST method")
        if not len(args) == 1:
            raise ValidationError("EmbeddingsResource expects texts as a single argument")
        if not isinstance(args[0], dict):
            raise ValidationError("EmbeddingsResource expected texts as a dict where the keys are hashes of the texts")
        if kwargs:
            raise ValidationError("EmbeddingsResource didn't expect kwargs")

    @staticmethod
    def prepare_text_fragments(texts):
        return {
            sha1(text.encode("utf-8")).hexdigest(): text
            for text in texts
        }

    @classmethod
    def create_text_payloads(cls, texts):
        encoding = tiktoken.encoding_for_model(cls.MODEL)
        text_sizes = [
            [len(encoding.encode(text)), key, text]
            for key, text in texts.items()
        ]
        text_sizes.sort(key=itemgetter(0), reverse=True)
        payloads = []
        while len(text_sizes):
            text_size = text_sizes.pop(0)
            payload_size = text_size[0]
            payload = [
                text_size[1:]
            ]
            while payload_size <= cls.MODEL_MAX_TOKENS:
                next_index = next(
                    (ix for ix, text_size in enumerate(text_sizes)
                     if (payload_size + text_size[0]) <= cls.MODEL_MAX_TOKENS),
                    None
                )
                if next_index is None:
                    break
                text_size = text_sizes.pop(next_index)
                payload_size += text_size[0]
                payload.append(text_size[1:])
            payloads.append(payload)
        return payloads

    def data(self, **kwargs):
        return super().data(model=self.MODEL, encoding_format="float")

    @staticmethod
    def text_payload_to_data(payload) -> list[str]:
        return [
            item[1]  # contains the text
            for item in payload
        ]

    def _create_request(self, method, *args, **kwargs):
        request = super()._create_request(method, *args, **kwargs)
        texts = args[0]
        payloads = self.create_text_payloads(texts)
        request["payloads"] = payloads
        request["payload_index"] = 0
        request["json"]["input"] = self.text_payload_to_data(payloads[0])
        return request

    @property
    def content(self):
        content_type, data = super().content
        if not data:
            return content_type, data
        raw_embeddings = data["data"]
        payload = self.request["payloads"][self.request["payload_index"]]
        embeddings = {
            text_info[0]: embedding["embedding"]
            for text_info, embedding in zip(payload, raw_embeddings)
        }
        return content_type, embeddings
