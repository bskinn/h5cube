# ------------------------------------------------------------------------------
# Name:        tests
# Purpose:     Master script for h5cube testing suite
#
# Author:      Brian Skinn
#                bskinn@alum.mit.edu
#
# Created:     29 Aug 2016
# Copyright:   (c) Brian Skinn 2016
# License:     The MIT License; see "LICENSE.txt" for full license terms
#                   and contributor agreement.
#
#       http://www.github.com/bskinn/h5cube
#
# ------------------------------------------------------------------------------


class AP(object):
    """ Container for arguments for selecting test suites.

    Also includes PFX, a helper string for substitution/formatting.

    """
    ALL = 'all'
    CMDLINE = 'cmdline'
    FUNCTIONS = 'functions'

    PFX = "--{0}"


def get_parser():
    import argparse

    # Create the parser
    prs = argparse.ArgumentParser(description="Run tests for h5cube")

    # Create test groups
    gp_global = prs.add_argument_group(title="Test selection options")

    # Verbosity argument
    prs.add_argument('-v', action='store_true',
                     help="Show verbose output")

    # All tests in a single group for now; project isn't big yet
    gp_global.add_argument(AP.PFX.format(AP.ALL),
                     action='store_true',
                     help="Run all tests (overrides any other selections)")
    gp_global.add_argument(AP.PFX.format(AP.CMDLINE),
                     action='store_true',
                     help="Run tests of commandline interface")
    gp_global.add_argument(AP.PFX.format(AP.FUNCTIONS),
                     action='store_true',
                     help="Run tests of h5cube internal functionality")

    # Return the parser
    return prs


def main():
    import h5cube.test
    import sys
    import unittest as ut

    # Retrieve the parser
    prs = get_parser()

    # Pull the dict of stored flags, saving the un-consumed args, and
    # update sys.argv
    ns, args_left = prs.parse_known_args()
    params = vars(ns)
    sys.argv = sys.argv[:1] + args_left

    # Create the empty test suite
    ts = ut.TestSuite()

    # All tests in one group for now
    if any(params[k] for k in [AP.ALL, AP.CMDLINE]):
        ts.addTest(h5cube.test.h5cube_cmdline.suite())

    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS]):
        ts.addTest(h5cube.test.h5cube_functions.suite())

    # Create the test runner and execute
    ttr = ut.TextTestRunner(buffer=True,
                            verbosity=(2 if params['v'] else 1))
    success = ttr.run(ts).wasSuccessful()

    # Return based on success result (enables tox)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
