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

If the relevant PRs get accepted upstream, then this will revert to the upstream fork.

## Installation

pip install kubernetes-validate

*Note:* This package is *HUGE*, even though it's very much cut down from kubernetes-json-schema.
It will take up about 300MB on disk. I will look at reducing that by deduplicating schema files if possible.
Any suggestions that would reduce disk usage and package size would be gratefully received!

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
                        Defaults to 1.11.0
  --strict              whether to use strict validation, rejecting unexpected
                        properties
  --version             show program's version number and exit
```

e.g.

```
$ kubernetes-validate -k 1.9.9 --strict resource.yml
```

### Python

```
from __future__ import print_function
import kubernetes_validate
import yaml

try:
    data = yaml.load(open('resource.yaml').read())
    kubernetes_validate.validate(data, '1.9.9', strict=True)
except kubernetes_validate.ValidationError as e:
    print(''. join(e.path), e.message)
```

### Examples

```
$ kubernetes-validate -k 1.9.9 examples/kuard-extra-property.yaml
INFO  examples/kuard-extra-property.yaml passed against version 1.9.9
```

```
$ kubernetes-validate --strict examples/kuard-extra-property.yaml
ERROR examples/kuard-extra-property.yaml did not validate against version 1.11.0: spec.selector: Additional properties are not allowed ('unwanted' was unexpected)
```

```
$ kubernetes-validate examples/kuard-invalid-type.yaml
ERROR examples/kuard-invalid-type.yaml did not validate against version 1.11.0: spec.replicas: 'hello' is not of type u'integer'
```

