from __future__ import print_function

import jsonschema
import pkg_resources
import yaml


class ValidationError(Exception):
    pass


def latest_version():
    versions = sorted(pkg_resources.resource_listdir('kubernetes_validate', '/kubernetes-json-schema'))
    return versions[-1]


def validate(data, version, strict=False):
    try:
        schema_filename = 'v%s-local'
        if strict:
            schema_filename += '-strict'
        schema_file = pkg_resources.resource_filename('kubernetes_validate', schema_filename)

        with open(schema_file) as f:
            schema = json.load(f.read())
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(e)
