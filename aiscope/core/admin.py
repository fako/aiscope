from django.contrib import admin

from datagrowth.resources.admin import HttpResourceAdmin

from core.models import OpenaiEmbeddingsResource, OpenaiPromptResource


admin.site.register(OpenaiEmbeddingsResource, HttpResourceAdmin)
admin.site.register(OpenaiPromptResource, HttpResourceAdmin)
