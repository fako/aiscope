import re
from dateutil.parser import parse as date_parser


class VoteRecordsExtractor:

    session_pattern = r"\D*(?P<sitting>\d+)\D*(?P<item>\d+)"

    @classmethod
    def _extract_description_value(cls, el, term):
        description_term = el.find("dt", text=term)
        description_value = description_term.find_next_sibling("dd")
        return description_value.text.strip()

    @classmethod
    def get_vote_records(cls, soup):
        result_links = soup.find_all("a", attrs={"class": "result--subtitle"})
        for result_link in result_links:
            if "stemming" not in result_link.text.lower():
                continue
            yield result_link.parent.parent  # should be the <li> tag of the search result

    @classmethod
    def get_url(cls, soup, el):
        link_tag = el.find("a")
        return f"https://zoek.officielebekendmakingen.nl/{link_tag["href"]}"

    @classmethod
    def get_date(cls, soup, el):
        dutch_date = cls._extract_description_value(el, "Datum document")
        date = date_parser(dutch_date, dayfirst=True)
        return date.strftime("%Y-%m-%d")

    @classmethod
    def get_parliamentary_session(cls, soup, el):
        return cls._extract_description_value(el, "Vergaderjaar")

    @classmethod
    def get_sitting(cls, soup, el):
        raw_session = cls._extract_description_value(el, "Vergadernummer")
        session_match = re.match(cls.session_pattern, raw_session)
        return f"{session_match.group("sitting")}-{session_match.group("item")}"

    @classmethod
    def get_political_body(cls, soup, el):
        return cls._extract_description_value(el, "Organisatie")


VOTE_RECORDS_OBJECTIVE = {
    "@": VoteRecordsExtractor.get_vote_records,
    "url": VoteRecordsExtractor.get_url,
    "date": VoteRecordsExtractor.get_date,
    "parliamentary_session": VoteRecordsExtractor.get_parliamentary_session,
    "sitting": VoteRecordsExtractor.get_sitting,
    "political_body": VoteRecordsExtractor.get_political_body,
}
