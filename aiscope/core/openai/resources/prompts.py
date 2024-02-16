import json
from enum import Enum
from copy import deepcopy
import tiktoken

from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError

from datagrowth.exceptions import DGResourceException
from datagrowth.resources.http import HttpResource


class MaxTokensExceeded(DGResourceException):
    pass


class InvalidChatGPTOption(DGResourceException):
    pass


class OpenaiPromptResource(HttpResource):

    CONFIG_NAMESPACE = "prompt_resource"

    MODEL = "gpt-3.5-turbo-0125"
    MODEL_MAX_TOKENS = 16385
    MODEL_MAX_OUTPUT_TOKENS = 4096
    MODEL_OPTIONS = ["n", "temperature", "top_p"]

    URI_TEMPLATE = "https://api.openai.com/v1/chat/completions"
    HEADERS = {
        "Content-Type": "application/json"
    }

    class ErrorCodes(Enum):
        TEMPLATE_DOES_NOT_EXIST = 1
        TEMPLATE_SYNTAX_ERROR = 2
        MAX_TOKENS_EXCEEDED = 3
        INVALID_CHATGPT_OPTION = 4
        CONTENT_FILTER = 5

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.config.openai_api_key}"
        }

    def validate_input(self, method, *args, **kwargs):
        if method != "post":
            raise ValidationError("PromptResource only supports POST method")
        if not len(args) == 1:
            raise ValidationError("PromptResource expects template name as a single argument")
        template_name = args[0]
        if not isinstance(template_name, str):
            raise ValidationError("PromptResource expected template name to be a string")
        if not template_name.endswith(".tpl"):
            raise ValidationError("PromptResource expected template name to have the .tpl or json.tpl extension")

    def validate_request(self, request, validate_input=True):
        request = super().validate_request(request, validate_input=validate_input)
        # Check that no prohibited options have leaked into the request
        for option in request["json"]:
            if option not in self.MODEL_OPTIONS and \
                    option not in ["model", "messages", "max_tokens", "response_format"]:
                raise ValueError(f"PromptResource received illegal option: {option}")
        # Check that token_count is present and valid or cancel the request
        if validate_input and not request["token_count"] and not request["cancel"]:
            request["cancel"] = True
        # Return the possibly canceled request
        return request

    def parse_inputs(self, template_name, template_context, options):
        # The options will be sent to OpenAI with the request along with required fields.
        data = deepcopy(options)
        # We parse the template to get the prompt
        template = get_template(template_name)
        message = template.render(context=template_context)
        # We make sure that the prompt falls within acceptable boundaries
        encoding = tiktoken.encoding_for_model(self.MODEL)
        token_count = len(encoding.encode(message))
        if token_count > self.MODEL_MAX_TOKENS:
            raise MaxTokensExceeded(
                f"Token count {token_count} exceeds max tokens {self.MODEL_MAX_TOKENS}",
                resource=self
            )
        # Update data with required fields and return
        data.update({
            "model": self.MODEL,
            "messages": [{"role": "user", "content": message}]
        })
        if template_name.endswith(".json.tpl"):
            data["response_format"] = {"type": "json_object"}
        return data, token_count

    def _create_request(self, method, *args, **kwargs):
        data = deepcopy(self.config.get("options", {}))
        token_count = None
        cancel = False
        try:
            data, token_count = self.parse_inputs(args[0], kwargs, self.config.get("options", {}))
        except TemplateDoesNotExist:
            cancel = True
            self.set_error(self.ErrorCodes.TEMPLATE_DOES_NOT_EXIST.value)
        except TemplateSyntaxError:
            cancel = True
            self.set_error(self.ErrorCodes.TEMPLATE_SYNTAX_ERROR.value)
        except MaxTokensExceeded:
            cancel = True
            self.set_error(self.ErrorCodes.MAX_TOKENS_EXCEEDED.value)
        request = super()._create_request(method, *args, **data)
        request["cancel"] = cancel
        request["token_count"] = token_count
        request["kwargs"] = kwargs
        return request

    def handle_errors(self):
        content_type, data = super().content
        if not data:
            return
        # Check if all messages came back ok and return if so
        is_success = all((choice["finish_reason"] == "stop" for choice in data["choices"]))
        if is_success:
            return True
        # Take the first error message and set that as the resource state
        error = next((choice for choice in data["choices"] if choice["finish_reason"] != "stop"))
        if error["finish_reason"] == "length":
            self.set_error(self.ErrorCodes.MAX_TOKENS_EXCEEDED.value)
        if error["finish_reason"] == "content_filter":
            self.set_error(self.ErrorCodes.CONTENT_FILTER.value)
        return False

    def _send(self):
        if self.request["cancel"]:
            return
        super()._send()

    @property
    def content(self):
        content_type, data = super().content
        if not data:
            return content_type, data
        messages = [
            choice["message"]["content"]
            for choice in data["choices"] if choice["finish_reason"] == "stop"
        ]
        if "response_format" in self.request["json"]:
            content_type = "application/json"
            messages = [
                json.loads(message)
                for message in messages
            ]
        else:
            content_type = "text/plain"
        return (content_type, messages[0],) if len(messages) == 1 else (content_type, messages,)
