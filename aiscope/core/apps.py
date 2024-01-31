from django.conf import settings
from django.apps import AppConfig
from django.core.checks import Error, register, Tags

from datagrowth.configuration import register_defaults


def api_key_system_check(app_configs, **kwargs):
    errors = []
    if not settings.OPENAI_API_KEY:
        errors.append(
            Error(
                "Settings doesn't specify an API key for OpenAI.",
                hint="Set the OPENAI_API_KEY variable in your .env file.",
                obj=None,
                id="core.E001",
            )
        )
    return errors


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        register(api_key_system_check, Tags.compatibility)
        register_defaults("global", {
            "openai_api_key": settings.OPENAI_API_KEY
        })
