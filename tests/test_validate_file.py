import os
import kubernetes_validate

parent = os.path.dirname(__file__)


def test_validate_resource_file():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'resource.yaml'), '1.22.0',
                                           strict=False, quiet=True, no_warn=True)
    assert (rc == 0)


def test_validate_multi_resource_file():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'kuard-all.yaml'), '1.22.0',
                                           strict=False, quiet=True, no_warn=True)
    assert (rc == 1)


def test_validate_strict_file():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'kuard-extra-property.yaml'), '1.22.0',
                                           strict=True, quiet=True, no_warn=True)
    assert (rc == 1)


def test_validate_invalid_file():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'kuard-invalid-type.yaml'), '1.22.0',
                                           strict=False, quiet=True, no_warn=True)
    assert (rc == 1)


def test_validate_madeup_file():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'kuard-made-up-kind.yaml'), '1.22.0',
                                           strict=False, quiet=True, no_warn=True)
    assert (rc == 0)


def test_validate_version_too_new():
    rc = kubernetes_validate.validate_file(os.path.join(parent, 'resource.yaml'), '1.99.0',
                                           strict=False, quiet=True, no_warn=True)
    assert (rc == 2)
