from hashlib import sha1

from datagrowth.datatypes import DatasetVersionBase, CollectionBase, DocumentBase

from dutch_parliament.constants import PremiseTypes, ActionTypes


class DatasetVersion(DatasetVersionBase):
    pass


class Collection(CollectionBase):

    @property
    def documents(self):
        return self.document_set


class Document(DocumentBase):

    def get_motion_argument_text(self) -> str | None:
        if not (action := self.properties.get("action")):
            return

        argument = ""

        for premise_type, premise in self.properties.get("premises", []):
            premise_type = PremiseTypes(premise_type)
            if premise_type == PremiseTypes.OBSERVATION:
                argument += f"Constaterende dat {premise};\n\n"
            elif premise_type == PremiseTypes.CONSIDERATION:
                argument += f"Overwegende dat {premise};\n\n"
            elif premise_type == PremiseTypes.OPINION:
                argument += f"Van mening dat {premise};\n\n"

        action_type = ActionTypes(action["type"])
        if not action["points"]:
            action_text = action["text"]
        else:
            action_text = f"{action["text"]}:\n\n"
            for point in action["points"]:
                action_text += f"* {point}\n"
        if action_type == ActionTypes.REQUEST:
            argument += f"Verzoekt {action["audience"]} om {action_text}"
        elif action_type == ActionTypes.SUGGESTION:
            argument += f"Doet {action["audience"]} de suggestie om {action_text}"

        return argument.strip()

    def get_claim_texts(self) -> dict[str, str] | None:
        if not (action := self.properties.get("action")):
            return

        texts = {
            sha1(action["text"].encode("utf-8")).hexdigest(): action["text"]
        }
        for _, premise in self.properties.get("premises"):
            key = sha1(premise.encode("utf-8")).hexdigest()
            texts[key] = premise
        for point in action["points"]:
            key = sha1(point.encode("utf-8")).hexdigest()
            texts[key] = point

        return texts

    @property
    def has_motion_texts(self) -> bool:
        return bool(self.derivatives.get("dutch_parliament.get_motion_texts"))
