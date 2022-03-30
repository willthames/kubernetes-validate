#!/usr/bin/env python

from __future__ import print_function

import argparse
import errno
import sys

import kubernetes_validate.utils as utils
from kubernetes_validate.version import __version__


def main():
    parser = argparse.ArgumentParser(description='validate a kubernetes resource definition')
    parser.add_argument('-k', '--kubernetes-version', action='append',
                        help='version of kubernetes against which to validate. Defaults to %s' %
                        utils.latest_version())
    parser.add_argument('--strict', action='store_true', default=False,
                        help='whether to use strict validation, rejecting unexpected properties')
    parser.add_argument('--quiet', action='store_true', default=False,
                        help='whether to only output warnings/failures')
    parser.add_argument('--no-warn', action='store_true', default=False,
                        help='whether to hide warnings')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('filenames', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if not args.filenames:
        parser.print_help()
        return 0

    rc = 0
    for filename in args.filenames:
        for version in args.kubernetes_version or [utils.latest_version()]:
            rc |= utils.validate_file(filename, version, args.strict, args.quiet, args.no_warn)

    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except IOError as exc:
        if exc.errno != errno.EPIPE:
            raise
    except RuntimeError as e:
        raise SystemExit(str(e))
