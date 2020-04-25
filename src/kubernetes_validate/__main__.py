#!/usr/bin/env python

from __future__ import print_function

import argparse
import errno
import sys
import yaml

import kubernetes_validate.utils as utils
from kubernetes_validate.version import __version__


def kn(resource):
    return "%s/%s" % (resource["kind"].lower(), resource["metadata"]["name"])


def main():
    parser = argparse.ArgumentParser(description='validate a kubernetes resource definition')
    parser.add_argument('-k', '--kubernetes-version', action='append',
                        help='version of kubernetes against which to validate. Defaults to %s' %
                        utils.latest_version())
    parser.add_argument('--strict', action='store_true', default=False,
                        help='whether to use strict validation, rejecting unexpected properties')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('filenames', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if not args.filenames:
        parser.print_help()
        return 0

    rc = 0
    for filename in args.filenames:
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

        for version in args.kubernetes_version or [utils.latest_version()]:
            for resource in data:
                try:
                    utils.validate(resource, version, args.strict)
                    print("INFO %s passed for resource %s against version %s" %
                          (filename, kn(resource), version))
                except utils.ValidationError as e:
                    print("ERROR %s did not validate for resource %s against version %s: %s: %s" %
                          (filename, kn(resource), version, '.'.join([str(item) for item in e.path]),
                           e.message))
                    rc = 1
                except (utils.SchemaNotFoundError, utils.InvalidSchemaError,
                        utils.VersionNotSupportedError) as e:
                    print("ERROR %s" % e.message)
                    rc = 2
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except IOError as exc:
        if exc.errno != errno.EPIPE:
            raise
    except RuntimeError as e:
        raise SystemExit(str(e))
