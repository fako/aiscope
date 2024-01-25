from django.contrib import admin

from datagrowth.admin import DataStorageAdmin, DocumentAdmin, HttpResourceAdmin

from political_discourse.models import (DutchParliamentMotionsDataset,
                                        MotionDatasetVersion, MotionCollection, MotionDocument,
                                        DutchParlementRecordSearch, DutchParlementRecord)


admin.site.register(DutchParliamentMotionsDataset, DataStorageAdmin)

admin.site.register(MotionDatasetVersion, DataStorageAdmin)
admin.site.register(MotionCollection, DataStorageAdmin)
admin.site.register(MotionDocument, DocumentAdmin)

admin.site.register(DutchParlementRecordSearch, HttpResourceAdmin)
admin.site.register(DutchParlementRecord, HttpResourceAdmin)
