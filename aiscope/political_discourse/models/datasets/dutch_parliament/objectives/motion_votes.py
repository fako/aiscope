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
    version: MotionVersion
    motion: bs4.Tag
    vote: bs4.Tag


class MotionVotesExtractor:

    approve_factions_pattern = r".*fracties van(?P<factions>.*) voor"
    reject_factions_pattern = r".*fracties van(?P<factions>.*) ertegen"

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
    def find_vote_paragraph(cls, motion_paragraph: bs4.Tag, motion_version: MotionVersion):
        vote_paragraph = None
        match motion_version:
            case MotionVersion.MODERN:
                vote_paragraph = motion_paragraph.parent.find_next_sibling("div").find("div").find("p")
            case MotionVersion.PLAIN_TEXT:
                vote_paragraph = motion_paragraph.parent.find_next_sibling("div").find("p").find_next_sibling("p")
            case _:
                pass
        return vote_paragraph

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
            vote_paragraph = cls.find_vote_paragraph(motion_paragraph, motion_version)
            yield MotionVoteParagraphs(
                version=motion_version,
                motion=motion_paragraph,
                vote=vote_paragraph
            )

    @classmethod
    def get_url(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        href = None
        match paragraphs.version:
            case MotionVersion.MODERN:
                href = paragraphs.motion.find("a")["href"]
            case MotionVersion.PLAIN_TEXT:
                record_id_match = re.match(cls.record_id_pattern, paragraphs.motion.text, re.IGNORECASE | re.DOTALL)
                href = f"kst-{record_id_match.group("record")}-{record_id_match.group("section")}.html"
            case _:
                pass
        return f"https://zoek.officielebekendmakingen.nl/{href}" if href else None

    @classmethod
    def get_approve_factions(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        approve_factions_match = re.match(cls.approve_factions_pattern, paragraphs.vote.text, re.IGNORECASE | re.DOTALL)
        return cls.parse_factions_match(approve_factions_match)

    @classmethod
    def get_reject_factions(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        if "overige fracties" in paragraphs.vote.text:
            return
        reject_factions_match = re.match(cls.reject_factions_pattern, paragraphs.vote.text, re.IGNORECASE | re.DOTALL)
        return cls.parse_factions_match(reject_factions_match)

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
    "url": MotionVotesExtractor.get_url,
    "approve_factions": MotionVotesExtractor.get_approve_factions,
    "reject_factions": MotionVotesExtractor.get_reject_factions,
    "outcome": MotionVotesExtractor.get_outcome,
}
