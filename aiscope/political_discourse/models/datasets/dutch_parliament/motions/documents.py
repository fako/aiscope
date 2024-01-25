from django.db import models

from datagrowth.datatypes import DatasetVersionBase, CollectionBase, DocumentBase

from political_discourse.models.datasets.dutch_parliament.constants import PremiseTypes, ActionTypes


class MotionDatastorageMixin:
    DATASET_VERSION_MODEL = "MotionDatasetVersion"
    COLLECTION_MODEL = "MotionCollection"
    DOCUMENT_MODEL = "MotionDocument"


class MotionDatasetVersion(MotionDatastorageMixin, DatasetVersionBase):

    @property
    def collections(self):
        return self.motioncollection_set

    @property
    def documents(self):
        return self.motiondocument_set


class MotionCollection(MotionDatastorageMixin, CollectionBase):

    dataset_version = models.ForeignKey(MotionDatasetVersion, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def documents(self):
        return self.motiondocument_set


class MotionDocument(MotionDatastorageMixin, DocumentBase):

    dataset_version = models.ForeignKey(MotionDatasetVersion, null=True, blank=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(MotionCollection, blank=True, null=True, on_delete=models.CASCADE)

    def get_motion_argument_text(self) -> str | None:
        if not (action := self.properties.get("action")) or not (premises := self.properties.get("premises")):
            return

        argument = ""

        for premise_type, premise in premises:
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
