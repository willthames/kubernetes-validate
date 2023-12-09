import os
import pytest
from kubernetes_validate import utils

parent = os.path.dirname(__file__)

VERSIONS = set(utils.all_versions())


def test_validate_valid_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'resource.yaml'))
    for version in VERSIONS:
        utils.validate(resources[0], version, strict=False)


def test_validate_strict_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-extra-property.yaml'))
    for version in VERSIONS:
        utils.validate(resources[0], version, strict=False)
    for version in VERSIONS:
        with pytest.raises(utils.ValidationError):
            utils.validate(resources[0], version, strict=True)


def test_validate_invalid_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-invalid-type.yaml'))
    for version in VERSIONS:
        with pytest.raises(utils.ValidationError):
            utils.validate(resources[0], version, strict=False)


def test_validate_madeup_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-made-up-kind.yaml'))
    for version in VERSIONS:
        with pytest.raises(utils.SchemaNotFoundError):
            utils.validate(resources[0], version, strict=False)


def test_validate_version_too_new():
    resources = utils.resources_from_file(os.path.join(parent, 'resource.yaml'))
    try:
        utils.validate(resources[0], '1.99.0', strict=False)
        assert False
    except utils.VersionNotSupportedError:
        assert True


def test_validate_object_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'resource.yaml'))

    class ResourceObject(object):
        def __init__(self, resource):
            self.resource = resource

        def to_dict(self):
            return self.resource

    for version in VERSIONS:
        utils.validate(ResourceObject(resources[0]), version, strict=False)
