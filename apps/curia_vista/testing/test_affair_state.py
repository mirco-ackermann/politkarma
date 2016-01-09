from unittest import TestCase

from apps.curia_vista.models import AffairState


class TestAffairState(TestCase):
    def setUp(self):
        self.T = AffairState(id=14, updated='2010-12-26T13:05:26Z', code='XYZ', name='XYZ')

    def test___str__(self):
        self.assertEqual('XYZ', str(self.T))
