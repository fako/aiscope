from enum import Enum
import re
from dataclasses import dataclass
import bs4


class MotionVersion(Enum):
    MODERN = "modern"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MotionVoteParagraphs:
    is_faction_vote: bool
    version: MotionVersion
    motion: bs4.Tag
    vote: bs4.Tag


class MotionVotesExtractor:

    approve_factions_pattern = r".*fracties van(?P<factions>.*?) voor"
    reject_factions_pattern = r".*fracties van(?P<factions>.*?) ertegen"
    approve_members_pattern = r".*vóór stemmen de leden: (?P<members>.*?) EOPT"
    reject_members_pattern = r".*tegen stemmen de leden: (?P<members>.*?) EOPT"

    record_id_pattern = r"\D*(?P<record>\d+)\D*(?P<section>\d+)"

    @classmethod
    def parse_factions_match(cls, match):
        factions_text = "".join(match.group("factions").split("\n"))
        raw_factions = factions_text.split(", ")
        last_factions = raw_factions.pop(-1)
        raw_factions += last_factions.split(" en ")
        factions = []
        for raw_faction in raw_factions:
            faction_parts = [
                part for part in raw_faction.split(" ") if part and part[0].isupper()
            ]
            faction = " ".join(faction_parts)
            factions.append(faction)
        return factions

    @classmethod
    def parse_members_match(cls, match):
        members_text = "".join(match.group("members").split("\n"))
        raw_members = members_text.split(", ")
        last_members = raw_members.pop(-1)
        raw_members += last_members.split(" en ")
        return raw_members

    @classmethod
    def find_vote_paragraph(cls, soup: bs4.BeautifulSoup, motion_paragraph: bs4.Tag, motion_version: MotionVersion):
        vote_paragraph = None
        is_faction_vote = True
        match motion_version:
            case MotionVersion.MODERN:
                vote_div = motion_paragraph.parent.find_next_sibling("div").find("div")
                if vote_div:
                    vote_paragraph = vote_div.find("p")
                else:
                    is_faction_vote = False
                    approve_div = motion_paragraph.parent.find_next_sibling("div")
                    reject_div = approve_div.find_next_sibling("div")
                    outcome_div = reject_div.find_next_sibling("div")
                    text = ""
                    for div in [approve_div, reject_div, outcome_div]:
                        paragraph = div.find("p")
                        if "voorzitter" in paragraph.text:
                            paragraph = paragraph.find_next_sibling("p")
                            text += paragraph.text.strip()
                        else:
                            text += paragraph.text.strip() + " EOPT "
                    vote_paragraph = soup.new_tag("p")
                    vote_paragraph.string = text.strip()
            case MotionVersion.PLAIN_TEXT:
                vote_paragraph = motion_paragraph.parent.find_next_sibling("div").find("p").find_next_sibling("p")
            case _:
                pass
        return vote_paragraph, is_faction_vote

    @classmethod
    def get_motion_votes(cls, soup: bs4.BeautifulSoup):
        motion_paragraphs = soup.find_all(
            lambda element: element.name == "p" and element.text.lower().startswith("in stemming komt")
        )
        for motion_paragraph in motion_paragraphs:
            motion_version = MotionVersion.UNKNOWN
            match motion_paragraph.parent["class"]:
                case ["draad"]:
                    motion_version = MotionVersion.PLAIN_TEXT
                case ["alineagroep"]:
                    motion_version = MotionVersion.MODERN
            vote_paragraph, is_faction_vote = cls.find_vote_paragraph(soup, motion_paragraph, motion_version)
            yield MotionVoteParagraphs(
                is_faction_vote=is_faction_vote,
                version=motion_version,
                motion=motion_paragraph,
                vote=vote_paragraph
            )

    @classmethod
    def get_vote_record_id(cls, soup: bs4.BeautifulSoup):
        identifier = soup.find("meta", attrs={"name": "DC.identifier"})
        return identifier["content"]

    @classmethod
    def get_motion_id(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        motion_id = None
        match paragraphs.version:
            case MotionVersion.MODERN:
                motion_id = paragraphs.motion.find("a")["href"].replace(".html", "")
            case MotionVersion.PLAIN_TEXT:
                record_id_match = re.match(cls.record_id_pattern, paragraphs.motion.text, re.IGNORECASE | re.DOTALL)
                motion_id = f"kst-{record_id_match.group("record")}-{record_id_match.group("section")}"
            case _:
                pass
        return motion_id

    @classmethod
    def get_url(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        motion_id = cls.get_motion_id(soup, paragraphs)
        return f"https://zoek.officielebekendmakingen.nl/{motion_id}.html" if motion_id else None

    @classmethod
    def get_approvals(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        if paragraphs.is_faction_vote:
            approve_factions_match = re.match(
                cls.approve_factions_pattern, paragraphs.vote.text,
                re.IGNORECASE | re.DOTALL
            )
            return cls.parse_factions_match(approve_factions_match)
        else:
            approve_members_match = re.match(
                cls.approve_members_pattern, paragraphs.vote.text,
                re.IGNORECASE | re.DOTALL
            )
            return cls.parse_members_match(approve_members_match)

    @classmethod
    def get_rejections(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        if paragraphs.is_faction_vote:
            if "overige fracties" in paragraphs.vote.text:
                return
            reject_factions_match = re.match(
                cls.reject_factions_pattern, paragraphs.vote.text,
                re.IGNORECASE | re.DOTALL
            )
            return cls.parse_factions_match(reject_factions_match)
        else:
            reject_members_match = re.match(
                cls.reject_members_pattern, paragraphs.vote.text,
                re.IGNORECASE | re.DOTALL
            )
            return cls.parse_members_match(reject_members_match)

    @classmethod
    def get_outcome(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        vote_words = [word for word in paragraphs.vote.text.split(" ") if word]
        outcome_word = vote_words[-1].strip(" .\n")
        outcome = None
        if outcome_word == "aangenomen":
            outcome = "approved"
        elif outcome_word == "verworpen":
            outcome = "rejected"
        return outcome


MOTION_VOTES_OBJECTIVE = {
    "@": MotionVotesExtractor.get_motion_votes,
    "#vote_record_id": MotionVotesExtractor.get_vote_record_id,
    "motion_id": MotionVotesExtractor.get_motion_id,
    "url": MotionVotesExtractor.get_url,
    "approvals": MotionVotesExtractor.get_approvals,
    "rejections": MotionVotesExtractor.get_rejections,
    "outcome": MotionVotesExtractor.get_outcome,
}
