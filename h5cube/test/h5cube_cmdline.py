# ------------------------------------------------------------------------------
# Name:        h5cube_cmdline
# Purpose:     Tests for the command line interface to h5cube
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

import unittest as ut
import unittest.mock as utm
from h5cube.test.h5cube_functions import SuperFunctionsTest


class SuperCmdlineTest(object):

    def store_args(self):
        # Store the cmdline args
        import sys
        self.argv_bak = sys.argv

    def restore_args(self):
        # Restore the cmdline args
        import sys
        sys.argv = self.argv_bak


@utm.patch('h5cube.h5cube.cube_to_h5')
class TestCmdlineCompressGood(SuperFunctionsTest, SuperCmdlineTest,
                              ut.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()
        cls.copy_scratch('.cube', include=('grid20',))

    def setUp(self):
        self.store_args()

    def tearDown(self):
        self.restore_args()

    @classmethod
    def tearDownClass(cls):
        cls.clear_scratch()

    def test_CmdlineCompress(self, cth_mock):
        from h5cube.h5cube import main as h5cube_main
        import numpy as np
        import sys

        # Arguments
        scrfname = self.scrfn('grid20.cube')
        baseargs = ['h5cube.py', scrfname]
        argsdict = {'noargs': [],
                    'nothresh': ['-n'],
                    'delsrc': ['-d'],
                    'comp5': ['-c', '5'],
                    'trunc3': ['-t', '3'],
                    'minmax': ['-m', '1e-5', '10'],
                    'ifac': ['-i', '0.002', '5'],
                    'mmax_s': ['-m', '-2e-2', '3e-1', '-s']}

            # ADD TESTS FOR PERMUTATIONS OF NEGATIVE VALUES IN SCIENTIFIC
            # NOTATION

        # Return values
        retsdict = {'noargs': {'cubepath': scrfname,
                               'comp': None, 'trunc': None,
                               'thresh': False, 'delsrc': False},
                    'nothresh': {'cubepath': scrfname,
                               'comp': None, 'trunc': None,
                               'thresh': False, 'delsrc': False},
                    'delsrc': {'cubepath': scrfname,
                               'comp': None, 'trunc': None,
                               'thresh': False, 'delsrc': True},
                    'comp5': {'cubepath': scrfname,
                              'comp': 5, 'trunc': None,
                              'thresh': False, 'delsrc': False},
                    'trunc3': {'cubepath': scrfname,
                               'comp': None, 'trunc': 3,
                               'thresh': False, 'delsrc': False},
                    'minmax': {'cubepath': scrfname,
                               'comp': None, 'trunc': None,
                               'thresh': True, 'delsrc' : False,
                               'signed': False,
                               'minmax': np.array([1e-5, 10])},
                    'ifac': {'cubepath': scrfname,
                             'comp': None, 'trunc': None,
                             'thresh': True, 'delsrc': False,
                             'signed': False,
                             'isofactor': np.array([0.002, 5.0])},
                    'mmax_s': {'cubepath': scrfname,
                               'comp': None, 'trunc': None,
                               'thresh': True, 'delsrc': False,
                               'signed': True,
                               'minmax': np.array([-2e-2, 3e-1])}}

        for name in argsdict:
            # Spoof argv
            sys.argv = baseargs + argsdict[name]

            # Call the commandline main function
            h5cube_main()

            # Store the kwargs passed; this relies on the cube_to_h5 code
            # being called in keyword-arg style by the _run_fxn_errcatch
            # function.
            kwargs = cth_mock.call_args[1]

            # Test identical keysets (symmetric difference is the empty set)
            with self.subTest(name=name + "_argmatch"):
                self.assertTrue(set(kwargs.keys()).symmetric_difference(
                                set(retsdict[name].keys())) == set())

            # Test each arg in the dicts
            for k in kwargs.keys():
                with self.subTest(name=name + '_' + k):
                    # Test the args
                    self.assertTrue(self.robust_equal(kwargs[k],
                                                      retsdict[name][k]))


def suite_cmdline_good():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestCmdlineCompressGood)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

