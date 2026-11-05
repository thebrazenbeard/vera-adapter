import unittest
import json
from dataclasses import asdict
from vera_adapter import AdapterRequest, AdapterResponse, validate_response

class ContractTests(unittest.TestCase):
    def test_matching_turn(self):
        req = AdapterRequest('t1', {'name':'Vera'}, (), ())
        self.assertEqual(validate_response(req, AdapterResponse('t1','hello','test','stub')).text, 'hello')
    def test_wrong_turn_rejected(self):
        req = AdapterRequest('t1', {}, (), ())
        with self.assertRaises(ValueError):
            validate_response(req, AdapterResponse('t2','hello','test','stub'))
    def test_identity_is_an_immutable_snapshot_not_a_live_caller_mapping(self):
        caller_identity = {'name': 'Vera'}
        request = AdapterRequest('t1', caller_identity, (), ())
        caller_identity['name'] = 'FORGED'
        self.assertEqual(request.identity['name'], 'Vera')
        with self.assertRaises(TypeError):
            request.identity['name'] = 'FORGED'
    def test_model_neutral_wire_dump_still_serializes(self):
        request = AdapterRequest('t1', {'name': 'Vera'}, (), ())
        self.assertEqual(asdict(request)['identity'], {'name': 'Vera'})
        self.assertEqual(json.loads(json.dumps(request.identity)), {'name': 'Vera'})

    def test_identity_mutation_methods_are_closed(self):
        request = AdapterRequest('t1', {'name': 'Vera'}, (), ())
        for mutate in (lambda d: d.update(name='Other'), lambda d: d.clear(),
                       lambda d: d.pop('name'), lambda d: d.setdefault('new', 'Other')):
            with self.subTest(mutate=mutate), self.assertRaises(TypeError):
                mutate(request.identity)
        self.assertEqual(request.identity, {'name': 'Vera'})

    def test_request_vectors_reject_caller_owned_mutable_lists(self):
        for field in ('continuity', 'conversation', 'capabilities', 'authority'):
            args = {'continuity': (), 'conversation': (), 'capabilities': (), 'authority': ()}
            args[field] = ['MUTABLE']
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                AdapterRequest('t1', {'name': 'Vera'}, **args)

    def test_request_vectors_require_canonical_string_tuples(self):
        for field in ('continuity', 'conversation', 'capabilities', 'authority'):
            args = {'continuity': (), 'conversation': (), 'capabilities': (), 'authority': ()}
            args[field] = ('valid', 123)
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                AdapterRequest('t1', {'name': 'Vera'}, **args)

    def test_identity_requires_string_keys_and_values(self):
        for bad_identity in ({1: 'Vera'}, {'name': 123}, {'name': True}):
            with self.subTest(identity=bad_identity), self.assertRaises((TypeError, ValueError)):
                AdapterRequest('t1', bad_identity, (), ())

if __name__ == '__main__': unittest.main()
