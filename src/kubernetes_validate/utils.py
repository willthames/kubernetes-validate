from __future__ import print_function

from distutils.version import LooseVersion
import json
import jsonschema
import os
import pkg_resources
import re
import yaml


ValidationError = jsonschema.ValidationError


def latest_version():
    schemas = pkg_resources.resource_listdir('kubernetes_validate', '/kubernetes-json-schema')
    version_regex = re.compile(r'^v([^-]*).*')
    versions = sorted([LooseVersion(version_regex.sub(r"\1", schema)) for schema in schemas if version_regex.match(schema)])
    return versions[-1]


def validate(data, version, strict=False):
    # strip initial v from version (I keep forgetting, so other people will too)
    if version.startswith('v'):
        version = version[1:]
    try:
        api_version = data['apiVersion'].replace('/', '-')
        schema_dir = 'v%s-local' % version
        if strict:
            schema_dir += '-strict'
        schema_file = pkg_resources.resource_filename('kubernetes_validate', '/kubernetes-json-schema/%s/%s-%s.json' %
                                                      (schema_dir, data['kind'].lower(), api_version))

        with open(schema_file) as f:
            schema = json.load(f)
        schema_dir = os.path.dirname(os.path.abspath(schema_file))
        resolver = jsonschema.RefResolver(base_uri = 'file://' + schema_dir + '/', referrer = schema)
        jsonschema.validate(data, schema, resolver=resolver)
    except jsonschema.ValidationError as e:
        raise
