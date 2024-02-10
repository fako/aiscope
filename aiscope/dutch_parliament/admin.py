from django.contrib import admin
from django.utils.html import format_html

from datagrowth.admin import DatasetAdmin, DatasetVersionAdmin, CollectionAdmin, TaskDocumentAdmin, HttpResourceAdmin

from dutch_parliament.models import (MotionsDataset, DatasetVersion, Collection, Document,
                                     DutchParlementRecordSearch, DutchParlementRecord)


class DutchParliamentRecordAdmin(TaskDocumentAdmin):

    list_display = TaskDocumentAdmin.list_display + ["content_link"]

    def content_link(self, obj):
        url = obj.properties.get("url")
        if not url:
            return format_html("-")
        return format_html(f"<a style='text-decoration: underline' target=_blank href={url}>{obj.identity} ↗</a>")


admin.site.register(MotionsDataset, DatasetAdmin)

admin.site.register(DatasetVersion, DatasetVersionAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Document, DutchParliamentRecordAdmin)

admin.site.register(DutchParlementRecordSearch, HttpResourceAdmin)
admin.site.register(DutchParlementRecord, HttpResourceAdmin)
