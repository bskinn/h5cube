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
    FUNCTIONS_MISC = 'functions_misc'
    FUNCTIONS_GOODH5 = 'functions_goodh5'
    FUNCTIONS_BADH5 = 'functions_badh5'
    FUNCTIONS_DATAH5 = 'functions_datah5'
    FUNCTIONS_CYCLEDH5 = 'functions_cycledh5'

    PFX = "--{0}"


def get_parser():
    import argparse

    # Create the parser
    prs = argparse.ArgumentParser(description="Run tests for h5cube")

    # Create test groups
    gp_global = prs.add_argument_group(title="Global test options")
    gp_fxns = prs.add_argument_group(title="Tests for API functions")
    gp_cmdline = prs.add_argument_group(title="Tests for commandline parsing")

    # Verbosity argument
    prs.add_argument('-v', action='store_true',
                     help="Show verbose output")

    # Groups without subgroups
    gp_global.add_argument(AP.PFX.format(AP.ALL),
                     action='store_true',
                     help="Run all tests (overrides any other selections)")
    gp_cmdline.add_argument(AP.PFX.format(AP.CMDLINE),
                     action='store_true',
                     help="Run tests of commandline interface")

    # API function tests
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS),
                     action='store_true',
                     help="Run all API function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_GOODH5),
                         action='store_true',
                         help="Run 'no-error' API function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_BADH5),
                         action='store_true',
                         help="Run 'error-expected' API function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_CYCLEDH5),
                         action='store_true',
                         help="Run multi-cycled API function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_DATAH5),
                         action='store_true',
                         help="Run API function data validation tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_MISC),
                         action='store_true',
                         help="Run tests of miscellaneous API functions")

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

    # All commandline tests in one group for now
    if any(params[k] for k in [AP.ALL, AP.CMDLINE]):
        ts.addTest(h5cube.test.h5cube_cmdline.suite())

    # API function tests split into groups
    # Expected-good
    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_GOODH5]):
        ts.addTest(h5cube.test.h5cube_functions.suite_goodh5())

    # Expected-bad
    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_BADH5]):
        ts.addTest(h5cube.test.h5cube_functions.suite_badh5())

    # Data validation tests
    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_DATAH5]):
        ts.addTest(h5cube.test.h5cube_functions.suite_datacheckh5())

    # Cycled execution tests
    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_CYCLEDH5]):
        ts.addTest(h5cube.test.h5cube_functions.suite_cycledh5())

    # Misc API tests
    if any(params[k] for k in [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_MISC]):
        ts.addTest(h5cube.test.h5cube_functions.suite_misc())

    # Create the test runner and execute
    ttr = ut.TextTestRunner(buffer=True,
                            verbosity=(2 if params['v'] else 1))
    success = ttr.run(ts).wasSuccessful()

    # Return based on success result (enables tox)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
