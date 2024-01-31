from django.contrib import admin

from datagrowth.admin import DataStorageAdmin, DocumentAdmin, HttpResourceAdmin

from dutch_parliament.models import (DutchParliamentMotionsDataset, DatasetVersion, Collection, Document,
                                     DutchParlementRecordSearch, DutchParlementRecord)


admin.site.register(DutchParliamentMotionsDataset, DataStorageAdmin)

admin.site.register(DatasetVersion, DataStorageAdmin)
admin.site.register(Collection, DataStorageAdmin)
admin.site.register(Document, DocumentAdmin)

admin.site.register(DutchParlementRecordSearch, HttpResourceAdmin)
admin.site.register(DutchParlementRecord, HttpResourceAdmin)
