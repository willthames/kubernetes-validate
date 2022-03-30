from __future__ import print_function

from distutils.version import LooseVersion
import json
import jsonschema
import os
import pkg_resources
import re
import sys
import yaml

from kubernetes_validate.version import __version__


class ValidationError(jsonschema.ValidationError):
    def __init__(self, caught, version):
        self.version = version
        for attr, value in caught.__dict__.items():
            self.__dict__[attr] = value


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


def major_minor(version):
    version_regex = re.compile(r'^(\d+\.\d+).*')
    return version_regex.sub(r"\1", version)


def latest_version():
    return all_versions()[-1]


def validate(data, desired_version, strict=False):
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
    except json.JsonDecodeError:
        raise InvalidSchemaError("Couldn't parse schema %s" % schema_file)
    finally:
        f.close()
    schema_dir = os.path.dirname(os.path.abspath(schema_file))
    resolver = jsonschema.RefResolver(base_uri='file:///' + schema_dir.replace("\\", "/") + '/',
                                      referrer=schema)

    try:
        jsonschema.validate(data, schema, resolver=resolver)
        return major_minor(version)
    except jsonschema.ValidationError as e:
        raise ValidationError(e, version=major_minor(version))
    except jsonschema.exceptions.RefResolutionError:
        raise


def kn(resource):
    return "%s/%s" % (resource["kind"].lower(), resource["metadata"]["name"])


def validate_resource(resource, filename, version, strict, quiet, no_warn):
    try:
        validated_version = validate(resource, version, strict)
        if not quiet:
            print(f"INFO {filename} passed for resource {kn(resource)} against version "
                  f"{validated_version}")
    except ValidationError as e:
        path = '.'.join([str(item) for item in e.path])
        print(f"ERROR {filename} did not validate for resource {kn(resource)} against version "
              f"{e.version}: {path}: {e.message}")
        return 1
    except (SchemaNotFoundError, InvalidSchemaError) as e:
        if not no_warn:
            print(f"WARN {filename} {e.message}")
    except VersionNotSupportedError:
        print(f"FATAL kubernetes-validate {__version__} does not support kubernetes version "
              f"{version}")
        return 2
    except Exception as e:
        print(f"ERROR {filename} could not be validated: {str(e)}")
        return 2
    return 0


def construct_value(load, node):
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(
            "while constructing a value",
            node.start_mark,
            "expected a scalar, but found %s" % node.id, node.start_mark
        )
    yield str(node.value)


def resources_from_file(filename):
    # Handle nodes that start with '='
    # See https://github.com/yaml/pyyaml/issues/89
    yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:value', construct_value)

    if filename == "-":
        f = sys.stdin
    else:
        try:
            f = open(filename)
        except Exception as e:
            raise SystemExit(f"Couldn't open file {filename} for reading: {str(e)}")
    try:
        # ignore empty yaml blocks
        data = [item for item in yaml.load_all(f.read(), Loader=yaml.SafeLoader) if item]
    except Exception as e:
        raise SystemExit(f"Couldn't parse YAML from file {filename}: {str(e)}")
    f.close()

    return data


def validate_file(filename, version, strict, quiet, no_warn):
    rc = 0
    for resource in resources_from_file(filename):
        rc |= validate_resource(resource, filename, version, strict, quiet, no_warn)
    return rc
