import re
from dataclasses import dataclass
import bs4


@dataclass(frozen=True, slots=True)
class MotionVoteParagraphs:
    motion: bs4.Tag
    vote: bs4.Tag


class MotionVotesExtractor:

    approve_factions_pattern = r".*fracties van(?P<factions>.*) voor"
    reject_factions_pattern = r".*fracties van(?P<factions>.*) ertegen"

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
    def get_motion_votes(cls, soup: bs4.BeautifulSoup):
        motion_paragraphs = soup.find_all(
            lambda element: element.name == "p" and element.text.lower().startswith("in stemming komt")
        )
        for motion_paragraph in motion_paragraphs:
            vote_paragraph = motion_paragraph.parent.find_next_sibling("div").find("div").find("p")
            yield MotionVoteParagraphs(
                motion=motion_paragraph,
                vote=vote_paragraph
            )

    @classmethod
    def get_url(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        link_tag = paragraphs.motion.find("a")
        return f"https://zoek.officielebekendmakingen.nl/{link_tag["href"]}"

    @classmethod
    def get_approve_factions(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
        approve_factions_match = re.match(cls.approve_factions_pattern, paragraphs.vote.text, re.IGNORECASE | re.DOTALL)
        return cls.parse_factions_match(approve_factions_match)

    @classmethod
    def get_reject_factions(cls, soup: bs4.BeautifulSoup, paragraphs: MotionVoteParagraphs):
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
