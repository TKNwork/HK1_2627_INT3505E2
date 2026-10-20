import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, FormatChecker
ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('name', ['book', 'author', 'review'])
def test_schema_and_examples(name):
    schema = json.loads((ROOT / 'schemas' / f'{name}.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    valid = json.loads((ROOT / 'examples' / f'{name}.valid.json').read_text())
    invalid = json.loads((ROOT / 'examples' / f'{name}.invalid.json').read_text())
    validator.validate(valid)
    assert list(validator.iter_errors(invalid))
    for key in schema['required']:
        assert list(validator.iter_errors({k:v for k,v in valid.items() if k != key}))
    assert list(validator.iter_errors(valid | {'unexpected': True}))

@pytest.mark.parametrize('name,key,value', [
    ('book','price',-1), ('book','author_ids',[]), ('book','isbn','abc'),
    ('author','website','not a url'), ('review','rating',6),
    ('review','created_at','bad date'), ('review','status','unknown')])
def test_constraints(name,key,value):
    schema = json.loads((ROOT / 'schemas' / f'{name}.schema.json').read_text())
    data = json.loads((ROOT / 'examples' / f'{name}.valid.json').read_text())
    data[key] = value
    assert list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
