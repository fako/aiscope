from enum import Enum


class ActionTypes(Enum):
    REQUEST = "request"
    SUGGESTION = "suggestion"


class PremiseTypes(Enum):
    OBSERVATION = "observation"
    CONSIDERATION = "consideration"
    OPINION = "opinion"
