from datagrowth.processors.resources.growth import HttpGrowthProcessor


class EmbeddingsGrowthProcessor(HttpGrowthProcessor):

    def reduce_contributions(self, contributions):
        contribution = {}
        for ctr in contributions:
            contribution.update(ctr)
        return contribution
