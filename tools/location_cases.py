#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministic composition cases for the two pattern-location fixes."""
from __future__ import annotations


def generate_cases() -> list[dict]:
    literals = (
        ('int', '-1', 'Int', True), ('int64', '-1L', 'Int64', True),
        ('hex', '-0x10', 'Int', True), ('double', '-1.5', 'Double', True),
        ('float', '-1.5F', 'Float', True), ('exponent', '-1.0e-3', 'Double', True),
        ('negative_zero', '-0.0', 'Double', True), ('spaced', '-  1', 'Int', True),
        ('positive_int', '1', 'Int', False), ('positive_double', '1.5', 'Double', False),
    )
    cases = []
    for literal_name, literal, typename, negative in literals:
        annotation = f'({literal} : {typename})'
        outer_annotation = f'({annotation} : {typename})'
        shapes = (
            ('plain', literal, [], False),
            ('annotated', annotation, [annotation], False),
            ('grouped', f'({annotation})', [annotation], True),
            ('constructor', f'Some(({annotation}))', [annotation], True),
            ('tuple', f'(({annotation}), _)', [annotation], True),
            ('nested_annotations', f'({outer_annotation})', [outer_annotation, annotation], True),
        )
        for shape, pattern, constraints, grouped in shapes:
            multiline = f'// 中文定位 😀\nfn f(x) {{\n  match x {{\n    {pattern} => 1\n    _ => 0\n  }}\n}}\n'
            layouts = (
                ('ascii_lf', f'fn f(x) {{ match x {{ {pattern} => 1; _ => 0 }} }}\n'),
                ('unicode_lf', multiline),
                ('unicode_crlf', multiline.replace('\n', '\r\n')),
                ('tabs_crlf', (f'fn f(x) {{\n\tmatch x {{\n\t\t// 模式前 😀\n'
                               f'\t\t{pattern} => 1\n\t\t_ => 0\n\t}}\n}}\n').replace('\n', '\r\n')),
            )
            for layout, source in layouts:
                cases.append({'name': f'{literal_name}__{shape}__{layout}', 'source': source,
                              'constants': [literal], 'constraints': constraints,
                              'literal': literal_name, 'shape': shape, 'layout': layout,
                              'requires_sign_fix': negative, 'requires_group_fix': grouped})
    assert len(cases) == 240 and len({c['name'] for c in cases}) == 240
    return cases


def expected_pass(case: dict, sign_fix: bool, group_fix: bool) -> bool:
    return ((sign_fix or not case['requires_sign_fix']) and
            (group_fix or not case['requires_group_fix']))
