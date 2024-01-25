import re
import bs4

from political_discourse.models.datasets.dutch_parliament.constants import ActionTypes, PremiseTypes


class MotionContentExtractor:

    request_pattern = "verzoekt (?P<audience>.*) om (?P<content>.*?)[,:]"
    suggestion_pattern = "doet (?P<audience>.*) de suggestie om (?P<content>.*?)[,:]"

    observation_pattern = r"constaterende,? dat (?P<content>.*?)[;]"
    consideration_pattern = r"overwegende,? dat (?P<content>.*?)[;]"
    opinion_pattern = r"van mening,? dat (?P<content>.*?)[;]"

    @classmethod
    def extract_text(cls, text: str):
        return " ".join(
            [part.strip() for part in text.split("\n")]
        )

    @classmethod
    def extract_element_text(cls, element: bs4.Tag):
        text = element.text.strip()
        return cls.extract_text(text)

    @classmethod
    def parse_content_paragraph(cls, paragraph: bs4.Tag, pattern: str) -> str | None:
        content_match = re.match(pattern, paragraph.text.strip().lower(), re.IGNORECASE | re.DOTALL)
        if not content_match:
            return
        content = content_match.group("content")
        return cls.extract_text(content)

    @classmethod
    def parse_action_match(cls, paragraph: bs4.Tag, match: re.Match, action_type: ActionTypes) -> dict | None:
        if not match:
            return
        action = cls.extract_text(match.group("content"))
        audience = match.group("audience")
        points_list = paragraph.find_next_sibling("ul")
        points = []
        if points_list:
            points = [
                cls.extract_element_text(point).strip(" ,;\u2022")
                for point in points_list.find_all("p")
            ]
        return {
            "type": action_type.value,
            "audience": audience,
            "text": action,
            "points": points
        }

    @classmethod
    def get_motion_content(cls, soup: bs4.BeautifulSoup) -> bs4.Tag:
        return soup.find("div", id="broodtekst")

    @classmethod
    def get_motion_id(cls, soup: bs4.BeautifulSoup) -> str:
        identifier = soup.find("meta", attrs={"name": "DC.identifier"})
        return identifier["content"]

    @classmethod
    def get_action(cls, soup: bs4.BeautifulSoup, content: bs4.Tag) -> dict:
        for paragraph in content.find_all("p"):
            action = None
            paragraph_text = paragraph.text.strip().lower()
            if request_match := re.match(cls.request_pattern, paragraph_text, re.IGNORECASE | re.DOTALL):
                action = cls.parse_action_match(paragraph, request_match, ActionTypes.REQUEST)
            elif suggestion_match := re.match(cls.suggestion_pattern, paragraph_text, re.IGNORECASE | re.DOTALL):
                action = cls.parse_action_match(paragraph, suggestion_match, ActionTypes.SUGGESTION)
            if action:
                return action

    @classmethod
    def get_premises(cls, soup: bs4.BeautifulSoup, content: bs4.Tag) -> list[tuple[str, str]]:
        premises = []
        for paragraph in content.find_all("p"):
            if observation_text := cls.parse_content_paragraph(paragraph, cls.observation_pattern):
                premises.append((PremiseTypes.OBSERVATION.value, observation_text,))
            elif consideration_text := cls.parse_content_paragraph(paragraph, cls.consideration_pattern):
                premises.append((PremiseTypes.CONSIDERATION.value, consideration_text,))
            elif opinion_text := cls.parse_content_paragraph(paragraph, cls.opinion_pattern):
                premises.append((PremiseTypes.OPINION.value, opinion_text,))
        return premises


MOTION_CONTENT_OBJECTIVE = {
    "@": MotionContentExtractor.get_motion_content,
    "#motion_id": MotionContentExtractor.get_motion_id,
    "action": MotionContentExtractor.get_action,
    "premises": MotionContentExtractor.get_premises,
}
