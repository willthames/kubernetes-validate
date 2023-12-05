from __future__ import print_function

import json
import os
import platform
import re
import sys
from distutils.version import LooseVersion
from typing import Any, Dict, Generator, List, Union

import jsonschema
import pkg_resources
import yaml

from kubernetes_validate.version import __version__


class ValidationError(jsonschema.ValidationError):
    def __init__(self, caught: Exception, version: str):
        self.version = version
        for attr, value in caught.__dict__.items():
            self.__dict__[attr] = value


class SchemaNotFoundError(Exception):
    def __init__(self, kind: str, version: str, api_version: str):
        self.kind = kind
        self.version = version
        self.api_version = api_version
        self.message = ("Couldn't find schema for kind %s with api version %s for kubernetes version %s" %
                        (self.kind, self.api_version, self.version))


class VersionNotSupportedError(Exception):
    def __init__(self, version: str):
        self.version = version
        self.message = ("kubernetes-validate does not support version %s" % self.version)


class InvalidSchemaError(Exception):
    def __init__(self, message: str):
        self.message = message


def all_versions() -> List[str]:
    schemas = pkg_resources.resource_listdir('kubernetes_validate', '/kubernetes-json-schema')
    version_regex = re.compile(r'^v([^-]*).*')
    return sorted([version_regex.sub(r"\1", schema) for schema in schemas if version_regex.match(schema)],
                  key=LooseVersion)


def major_minor(version: str) -> str:
    version_regex = re.compile(r'^(\d+\.\d+).*')
    return version_regex.sub(r"\1", version)


def latest_version() -> str:
    return all_versions()[-1]


def validate(data: Union[Dict[str, Any], Any], desired_version: str, strict: bool = False) -> str:
    if not isinstance(data, dict):
        try:
            data = data.to_dict()
        except AttributeError:
            raise TypeError("data must be a dict or object with a to_dict() method")
    # strip initial v from version (I keep forgetting, so other people will too)
    if desired_version.startswith('v'):
        desired_version = desired_version[1:]
    if major_minor(desired_version) > latest_version():
        raise VersionNotSupportedError(version=major_minor(desired_version))
    # actual schema version is the latest version that is not newer than the desired version
    version = [version for version in all_versions()
               if major_minor(version) <= major_minor(desired_version)][-1]
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
        raise SchemaNotFoundError(version=major_minor(desired_version), kind=data['kind'],
                                  api_version=data['apiVersion'])
    try:
        schema = json.load(f)
    except json.decoder.JSONDecodeError:
        raise InvalidSchemaError("Couldn't parse schema %s" % schema_file)
    finally:
        f.close()
    schema_dir = os.path.dirname(os.path.abspath(schema_file))

    uri_prefix = "file://"
    if platform.system() == 'Windows':
        uri_prefix += "/"

    resolver = jsonschema.RefResolver(base_uri=uri_prefix + schema_dir.replace("\\", "/") + '/',
                                      referrer=schema)

    try:
        jsonschema.validate(data, schema, resolver=resolver)
        return major_minor(version)
    except jsonschema.ValidationError as e:
        raise ValidationError(e, version=major_minor(version))
    except jsonschema.RefResolutionError:
        raise


def kn(resource: dict) -> str:
    return "%s/%s" % (resource["kind"].lower(), resource["metadata"]["name"])


def validate_resource(
    resource: dict,
    filename: str,
    version: str,
    strict: bool,
    quiet: bool,
    no_warn: bool,
) -> int:
    try:
        validated_version = validate(resource, version, strict)
        if not quiet:
            print("INFO %s passed for resource %s against version %s" %
                  (filename, kn(resource), validated_version))
    except ValidationError as e:
        path = '.'.join([str(item) for item in e.path])
        print("ERROR %s did not validate for resource %s against version %s: %s: %s" %
              (filename, kn(resource), e.version, path, e.message))
        return 1
    except (SchemaNotFoundError, InvalidSchemaError) as e:
        if not no_warn:
            print("WARN %s %s" % (filename, e.message))
    except VersionNotSupportedError:
        print("FATAL kubernetes-validate %s does not support kubernetes version %s" %
              (__version__, version))
        return 2
    except Exception as e:
        print("ERROR %s could not be validated: %s" % (filename, str(e)))
        return 2
    return 0


def construct_value(load: yaml.Loader, node: yaml.ScalarNode) -> Generator[str, None, None]:
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(
            "while constructing a value",
            node.start_mark,
            "expected a scalar, but found %s" % node.id, node.start_mark
        )
    yield str(node.value)


def resources_from_file(filename: str) -> List[Dict]:
    # Handle nodes that start with '='
    # See https://github.com/yaml/pyyaml/issues/89
    yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:value', construct_value)

    if filename == "-":
        f = sys.stdin
    else:
        try:
            f = open(filename)
        except Exception as e:
            raise SystemExit("Couldn't open file %s for reading: %s" % (filename, str(e)))
    try:
        # ignore empty yaml blocks
        data = [item for item in yaml.load_all(f.read(), Loader=yaml.SafeLoader) if item]
    except Exception as e:
        raise SystemExit("Couldn't parse YAML from file %s: %s" % (filename, str(e)))
    f.close()

    return data


def validate_file(
    filename: str, version: str, strict: bool, quiet: bool, no_warn: bool
) -> int:
    rc = 0
    for resource in resources_from_file(filename):
        rc |= validate_resource(
            resource=resource,
            filename=filename,
            version=version,
            strict=strict,
            quiet=quiet,
            no_warn=no_warn,
        )
    return rc
