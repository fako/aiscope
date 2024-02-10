from django.contrib import admin

from datagrowth.resources.admin import HttpResourceAdmin

from core.models import OpenaiEmbeddingsResource


admin.site.register(OpenaiEmbeddingsResource, HttpResourceAdmin)
