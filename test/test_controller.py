import unittest
from controller import Controller
from model import Model
class TestController(unittest.TestCase):
    def test_controller(self):
        model = Model('...')
        assert Controller(model)

