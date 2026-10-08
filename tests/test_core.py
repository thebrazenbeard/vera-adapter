import unittest
from vera_adapter import AdapterRequest, AdapterResponse, IdentityCapsule, SourceRef, VeraIR, validate_response

def request(turn_id: str) -> AdapterRequest:
    source = SourceRef("thebrazenbeard/vera-mono", "abc123", "identity.json")
    return AdapterRequest(turn_id, VeraIR(IdentityCapsule({"name": "Vera"}, (), sources=(source,))))

class ContractTests(unittest.TestCase):
    def test_matching_turn(self):
        req = request("t1")
        self.assertEqual(validate_response(req, AdapterResponse("t1","hello","test","stub")).text, "hello")
    def test_wrong_turn_rejected(self):
        req = request("t1")
        with self.assertRaises(ValueError):
            validate_response(req, AdapterResponse("t2","hello","test","stub"))

if __name__ == "__main__": unittest.main()
