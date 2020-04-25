from __future__ import print_function
import kubernetes_validate
import yaml

try:
    data = yaml.load(open('resource.yaml').read())
    kubernetes_validate.validate(data, '1.9.9', strict=True)
except kubernetes_validate.ValidationError as e:
    print(''. join(e.path), e.message)
