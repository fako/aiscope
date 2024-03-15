from copy import deepcopy

from django.test import TestCase

from datagrowth.processors import SeedingProcessorFactory

from dutch_parliament.models import MotionsDataset, Collection


class TestMotionsDataset(TestCase):

    start_date_input = {
        "$start_date": "2006-01-01"
    }
    dates_input = {
        "$start_date": "2006-01-01",
        "$end_date": "2010-12-31"  # motions discussed on the end date will be included
    }

    def test_get_signature_from_input(self):
        dataset = MotionsDataset()
        no_dates_signature = dataset.get_signature_from_input("Migratie en integratie")
        self.assertEqual(no_dates_signature, "Migratie en integratie")
        start_date_signature = dataset.get_signature_from_input("Migratie en integratie", **self.start_date_input)
        self.assertEqual(start_date_signature, "Migratie en integratie&start_date=2006-01-01")
        both_dates_signature = dataset.get_signature_from_input("Migratie en integratie", **self.dates_input)
        self.assertEqual(both_dates_signature, "Migratie en integratie&end_date=2010-12-31&start_date=2006-01-01")

    def test_get_seeding_factories(self):
        # Prepare data
        dataset = MotionsDataset(config=self.dates_input)
        collection = Collection(identifier="test")

        seeding_factories = dataset.get_seeding_factories()

        # Basic asserts
        self.assertIsInstance(seeding_factories, dict)
        self.assertEqual(len(seeding_factories), 5)
        # Check factory functioning
        for ix, factory_info in enumerate(seeding_factories.items()):
            signature, factory = factory_info
            year = 2006 + ix
            self.assertIsInstance(factory, SeedingProcessorFactory)
            processor = factory.build(collection=collection)
            start_date = processor.config.start_date
            end_date = processor.config.end_date
            self.assertEqual(start_date, f"{year}-01-01")
            self.assertEqual(end_date, f"{year}-12-31")
            self.assertEqual(signature, f"end_date={end_date}&start_date={start_date}")

    def test_get_seeding_factories_custom_end_date(self):
        # Prepare data
        dates = deepcopy(self.dates_input)
        dates["$end_date"] = "2010-08-15"
        dataset = MotionsDataset(config=dates)
        collection = Collection(identifier="test")

        seeding_factories = dataset.get_seeding_factories()

        # Asserts
        self.assertIn("end_date=2010-08-15&start_date=2010-01-01", seeding_factories)
        factory = seeding_factories["end_date=2010-08-15&start_date=2010-01-01"]
        processor = factory.build(collection=collection)
        self.assertEqual(processor.config.start_date, f"2010-01-01")
        self.assertEqual(processor.config.end_date, f"2010-08-15")
