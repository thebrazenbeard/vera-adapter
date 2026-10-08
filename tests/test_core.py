import unittest
from vera_adapter import AdapterRequest, AdapterResponse, validate_response

class ContractTests(unittest.TestCase):
    def test_matching_turn(self):
        req = AdapterRequest('t1', {'name':'Vera'}, (), ())
        self.assertEqual(validate_response(req, AdapterResponse('t1','hello','test','stub')).text, 'hello')
    def test_wrong_turn_rejected(self):
        req = AdapterRequest('t1', {}, (), ())
        with self.assertRaises(ValueError):
            validate_response(req, AdapterResponse('t2','hello','test','stub'))

if __name__ == '__main__': unittest.main()
