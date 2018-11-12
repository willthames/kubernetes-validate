from __future__ import print_function

from distutils.version import LooseVersion
import json
import jsonschema
import os
import pkg_resources
import re


ValidationError = jsonschema.ValidationError


class SchemaNotFoundError(Exception):
    def __init__(self, kind, version, api_version):
        self.kind = kind
        self.version = version
        self.api_version = api_version
        self.message = ("Couldn't find schema for kind %s with api version %s for kubernetes version %s" %
                        (self.kind, self.api_version, self.version))


class VersionNotSupportedError(Exception):
    def __init__(self, version):
        self.version = version
        self.message = ("kubernetes-validate does not support version %s" % self.version)


class InvalidSchemaError(Exception):
    def __init__(self, message):
        self.message = message


def all_versions():
    schemas = pkg_resources.resource_listdir('kubernetes_validate', '/kubernetes-json-schema')
    version_regex = re.compile(r'^v([^-]*).*')
    return sorted([version_regex.sub(r"\1", schema) for schema in schemas if version_regex.match(schema)],
                  key=LooseVersion)


def latest_version():
    return all_versions()[-1]


def validate(data, desired_version, strict=False):
    # strip initial v from version (I keep forgetting, so other people will too)
    if desired_version.startswith('v'):
        desired_version = desired_version[1:]
    # actual schema version is the latest version that is not newer than the desired version
    version = [version for version in all_versions() if version <= LooseVersion(desired_version)][-1]
    # Remove the trailing domain from the api version namespace and replace the / with -
    # e.g. rbac.authorization.k8s.io/v1 -> rbac-v1
    api_version = re.sub(r'^([^./]*)(?:\.[^/]*)?/', r'\1-', data['apiVersion'])
    schema_dir = 'v%s-local' % version
    if strict:
        schema_dir += '-strict'
    schema_file = pkg_resources.resource_filename('kubernetes_validate',
                                                  '/kubernetes-json-schema/%s/%s-%s.json' %
                                                  (schema_dir, data['kind'].lower(), api_version))

    try:
        f = open(schema_file)
    except IOError:
        if not os.path.exists(os.path.dirname(schema_file)):
            raise VersionNotSupportedError(version=desired_version)
        raise SchemaNotFoundError(version=desired_version, kind=data['kind'], api_version=data['apiVersion'])
    try:
        schema = json.load(f)
    except json.JsonDecodeError:
        raise InvalidSchemaError("Couldn't parse schema %s" % schema_file)
    finally:
        f.close()
    schema_dir = os.path.dirname(os.path.abspath(schema_file))
    resolver = jsonschema.RefResolver(base_uri='file://' + schema_dir + '/', referrer=schema)

    try:
        jsonschema.validate(data, schema, resolver=resolver)
    except jsonschema.ValidationError:
        raise
    except jsonschema.exceptions.RefResolutionError:
        raise
