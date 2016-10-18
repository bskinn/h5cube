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
    FUNCTIONS = 'fxn'
    FUNCTIONS_MISC = 'fxn_misc'
    FUNCTIONS_CGOOD = 'fxn_cgood'
    FUNCTIONS_CBAD = 'fxn_cbad'
    FUNCTIONS_CALL = 'fxn_call'
    FUNCTIONS_DGOOD = 'fxn_dgood'
    FUNCTIONS_DALL = 'fxn_dall'
    FUNCTIONS_DATA = 'fxn_data'
    FUNCTIONS_CYCLED = 'fxn_cycled'

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
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_CALL),
                         action='store_true',
                         help="Run all API compression function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_CGOOD),
                         action='store_true',
                         help="Run 'no-error' API compression function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_CBAD),
                         action='store_true',
                         help="Run 'error-expected' API compression "
                              "function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_DGOOD),
                         action='store_true',
                         help="Run 'no-error' API decompression function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_DALL),
                         action='store_true',
                         help="Run all API decompression function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_CYCLED),
                         action='store_true',
                         help="Run multi-cycled API function tests")
    gp_fxns.add_argument(AP.PFX.format(AP.FUNCTIONS_DATA),
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

    # Helper function for adding test suites. Just uses ts and params from
    # the main() function scope
    def addsuiteif(suite, flags):
        if any(params[k] for k in flags):
            ts.addTest(suite)

    # All commandline tests in one group for now
    addsuiteif(h5cube.test.h5cube_cmdline.suite(), [AP.ALL, AP.CMDLINE])

    # API function tests split into groups
    # Expected-good compression
    addsuiteif(h5cube.test.h5cube_functions.suite_goodcth(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_CALL, AP.FUNCTIONS_CGOOD])

    # Expected-bad compression
    addsuiteif(h5cube.test.h5cube_functions.suite_badcth(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_CALL, AP.FUNCTIONS_CBAD])

    # Expected-good decompression
    addsuiteif(h5cube.test.h5cube_functions.suite_goodhtc(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_DALL, AP.FUNCTIONS_DGOOD])

    # Data validation tests
    addsuiteif(h5cube.test.h5cube_functions.suite_datacheckh5(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_DATA])

    # Cycled execution tests
    addsuiteif(h5cube.test.h5cube_functions.suite_cycledh5(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_CYCLED])

    # Misc API tests
    addsuiteif(h5cube.test.h5cube_functions.suite_misc(),
               [AP.ALL, AP.FUNCTIONS, AP.FUNCTIONS_MISC])

    # Create the test runner and execute
    ttr = ut.TextTestRunner(buffer=True,
                            verbosity=(2 if params['v'] else 1))
    success = ttr.run(ts).wasSuccessful()

    # Return based on success result (enables tox)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
