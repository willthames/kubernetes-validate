# kubernetes-validate

kubernetes-validate validates Kubernetes resource definitions against the
declared Kubernetes schemas.

Based on Gareth Rushgrove's excellent work providing a basis for turning Kubernetes
Swagger API definitions into JSONSchema definitions, kubernetes-validate will report
on mismatches between schema defnition and resource definition

Note that this currently uses a fork of kubernetes-json-schema for the following reasons:
* Add API versions into schema names (built using https://github.com/garethr/openapi2jsonschema/pull/11)
* [Increase coverage of strict versions](https://github.com/garethr/kubernetes-json-schema/pull/8)
* [Update to latest Kubernetes released API versions](https://github.com/garethr/kubernetes-json-schema/pull/8)
* Provide local-strict schemas
* Reduce Kubernetes version support (v1.5 and v1.6 schemas are not included to reduce
  library size and schema build time)

Furthermore, the module now includes only the .0 API schemas, as they change so little within a Kubernetes
version (there are some differences but they seem to be mostly irrelevant to validation - e.g. description
updates). This has taken the module down from 300MB to less than 30MB.

If the relevant PRs get accepted upstream, then this will revert to the upstream fork.

## Installation

pip install kubernetes-validate

## Usage

### Command line

```
$ kubernetes-validate
usage: kubernetes-validate [-h] [-k KUBERNETES_VERSION] [--strict] [--version]
                           ...

validate a kubernetes resource definition

positional arguments:
  filenames

optional arguments:
  -h, --help            show this help message and exit
  -k KUBERNETES_VERSION, --kubernetes-version KUBERNETES_VERSION
                        version of kubernetes against which to validate.
                        Defaults to major/minor version of kubernetes-validate
                        (i.e. 1.22.1 supports kubernetes 1.22). Patch versions
                        of the version are ignored (1.22.4 validates against
                        1.22.0)
  --strict              whether to use strict validation, rejecting unexpected
                        properties
  --quiet               silences successful resources being displayed
  --version             show program's version number and exit
```

e.g.

```
$ kubernetes-validate -k 1.20 --strict resource.yml
```

### Python

```
from __future__ import print_function
import kubernetes_validate
import yaml

try:
    data = yaml.load(open('resource.yaml').read())
    kubernetes_validate.validate(data, '1.22', strict=True)
except kubernetes_validate.ValidationError as e:
    print(''. join(e.path), e.message)
```

### Examples

```
$ kubernetes-validate -k 1.13.6 examples/kuard-extra-property.yaml
INFO  examples/kuard-extra-property.yaml passed against version 1.13.6
```

```
$ kubernetes-validate --strict examples/kuard-extra-property.yaml
ERROR examples/kuard-extra-property.yaml did not validate against version 1.16.0: spec.selector: Additional properties are not allowed ('unwanted' was unexpected)
```

```
$ kubernetes-validate examples/kuard-invalid-type.yaml
ERROR examples/kuard-invalid-type.yaml did not validate against version 1.16.0: spec.replicas: 'hello' is not of type u'integer'
```

