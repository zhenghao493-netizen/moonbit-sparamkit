#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Small host tests for deterministic case generation and comparison checks."""
import copy
import unittest
from location_cases import generate_cases, expected_pass
from test_location_matrix import assess, first_difference, without_locations


class MatrixHarnessTests(unittest.TestCase):
    def test_unique_deterministic_cross_product(self):
        cases = generate_cases()
        self.assertEqual(cases, generate_cases())
        self.assertEqual(len(cases), 240)
        self.assertEqual(len({c['name'] for c in cases}), 240)
        self.assertEqual(len({c['source'] for c in cases}), 240)

    def test_controls_and_independent_fix_requirements(self):
        cases = generate_cases()
        self.assertEqual([sum(expected_pass(c,a,b) for c in cases)
                          for a,b in ((False,False),(True,False),(False,True),(True,True))],
                         [16,80,48,240])

    def test_crlf_and_unicode_are_kept_in_sources(self):
        for case in generate_cases():
            if 'crlf' in case['layout']:
                self.assertIn('\r\n', case['source'])
                self.assertNotIn('\n', case['source'].replace('\r\n',''))
            if case['layout'] != 'ascii_lf':
                self.assertIn('😀', case['source'])
            for value in case['constants']+case['constraints']:
                self.assertIn(value, case['source'])

    def test_raw_location_check_is_not_semantic_projection(self):
        a={'kind':'Pattern::Constant','loc':'1:1-1:3','value':-1}
        b=dict(a,loc='1:2-1:3')
        self.assertEqual(without_locations(a),without_locations(b))
        self.assertEqual(first_difference(a,b)['path'],'$.loc')
        self.assertNotEqual(without_locations(a),without_locations(dict(a,value=1)))

    def test_assessment_rejects_wrong_slice_and_missing_results(self):
        case=generate_cases()[0]
        parse={'ast':[], 'diagnostics':[], 'constants':case['constants'], 'constraints':[]}
        result={'name':case['name'],'parses':{k:copy.deepcopy(parse) for k in ('handrolled','moonyacc','cst')}}
        self.assertTrue(assess([case],[result],True,True)[0]['matches'])
        result['parses']['handrolled']['constants']=['1']
        self.assertFalse(assess([case],[result],True,True)[0]['matches'])
        with self.assertRaises(RuntimeError):
            assess([case],[],True,True)


if __name__=='__main__':
    unittest.main()
