from copy import copy
from datetime import datetime
from urlobject import URLObject

from django.db import models
from django.utils.timezone import make_aware

from datagrowth.resources import HttpResource, URLResource


class DutchParlementRecordSearch(HttpResource):  # rs.get("Migratie en integratie", "20220901", "20220930")

    uri = models.CharField(max_length=1024, db_index=True, default=None)

    URI_TEMPLATE = "https://zoek.officielebekendmakingen.nl/resultaten"

    DATE_FORMAT = "%Y-%m-%d"
    SEARCH_FILTERS = [
        '(c.product-area=="officielepublicaties")',
        '((dt.creator=="Tweede Kamer der Staten-Generaal")or(dt.creator=="Tweede Kamer OCV / UCV"))',
        '(w.publicatienaam=="Handelingen")'
    ]

    PARAMETERS = {
        "pg": 50,
        "col": "AlleParlementaireDocumenten",
        "svel": "Kenmerkendedatum",
        "svol": "Aflopend",
        "sf": "ru|Handeling",
    }

    def variables(self, *args):
        return {
            "url": [],
            "topic": args[0],
        }

    def parameters(self, topic, **kwargs):
        parameters = super().parameters()
        search_filters = copy(self.SEARCH_FILTERS)
        search_filters.append(f'(dt.subject="{topic}")')
        start_date = self.config.start_date
        last_year = datetime.now().year - 1
        default_end_date = make_aware(datetime(year=last_year, month=12, day=1)).strftime(self.DATE_FORMAT)
        end_date = self.config.get("end_date", default_end_date) or default_end_date
        date_range_filter = f'(dt.date>="{start_date}" and dt.date<="{end_date}")'
        search_filters.append(date_range_filter)
        parameters["q"] = "and".join(search_filters)
        return parameters

    def next_parameters(self):
        content_type, data = self.content
        next_link = data.find("a", id="id-page-next")
        if next_link is None:
            return None
        next_url = URLObject(next_link.get("href"))
        return {
            "pagina": next_url.query_dict["pagina"]
        }


class DutchParlementRecord(URLResource):
    pass
