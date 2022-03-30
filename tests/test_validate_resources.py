import os
from kubernetes_validate import utils

parent = os.path.dirname(__file__)


def test_validate_valid_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'resource.yaml'))
    utils.validate(resources[0], '1.22.0', strict=False)


def test_validate_strict_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-extra-property.yaml'))
    utils.validate(resources[0], '1.22.0', strict=False)
    try:
        utils.validate(resources[0], '1.22.0', strict=True)
        assert False
    except utils.ValidationError:
        assert True


def test_validate_invalid_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-invalid-type.yaml'))
    try:
        utils.validate(resources[0], '1.22.0', strict=False)
        assert False
    except utils.ValidationError:
        assert True


def test_validate_madeup_resource():
    resources = utils.resources_from_file(os.path.join(parent, 'kuard-made-up-kind.yaml'))
    try:
        utils.validate(resources[0], '1.22.0', strict=False)
        assert False
    except utils.SchemaNotFoundError:
        assert True


def test_validate_version_too_new():
    resources = utils.resources_from_file(os.path.join(parent, 'resource.yaml'))
    try:
        utils.validate(resources[0], '1.99.0', strict=False)
        assert False
    except utils.VersionNotSupportedError:
        assert True
