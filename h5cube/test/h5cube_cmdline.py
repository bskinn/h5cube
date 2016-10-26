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


class SuperCmdlineTest(SuperFunctionsTest):

    def store_args(self):
        # Store the cmdline args
        import sys
        self.argv_bak = sys.argv

    def restore_args(self):
        # Restore the cmdline args
        import sys
        sys.argv = self.argv_bak

    def good_test(self, ba, ad, kd, mo):
        """ Run expected-good commandline test.

        Parameters
        ----------
        ba :
            |dict| -- "Baseline" arguments to include in all calls

        ad :
            |dict| of |list| -- Commandline argument sets

        kd :
            |dict| of |dict| -- `kwargs` sets from mocked function calls
            (keys must be identical to those of `ad`)

        mo :
            :cls:`Mock` -- Mock object for the callable target
            from the commandline invocation

        """

        from h5cube.h5cube import main as h5cube_main
        import sys

        # Check each set of cmdline conditions
        for name in ad:
            # Spoof argv
            sys.argv = ba + ad[name]

            # Call the commandline main function
            h5cube_main()

            # Store the kwargs passed; this relies on the cube_to_h5 and
            # h5_to_cube code being called with all args specified with
            # keyword-arg syntax.
            kwargs = mo.call_args[1]

            # Test identical keysets (symmetric difference is the empty set)
            with self.subTest(name=name + "_argmatch"):
                self.assertTrue(set(kwargs.keys()).symmetric_difference(
                                set(kd[name].keys())) == set(),
                                msg="Keyset mismatch in test '{0}'".format(name))

            # Test each arg in the dicts
            for k in kwargs:
                with self.subTest(name=name + '__' + k):
                    # Test the args
                    self.assertTrue(self.robust_equal(kwargs[k],
                                                      kd[name][k]),
                                    msg="Mismatch in test '{0}' at key '{1}'"
                                        .format(name, k))


@utm.patch('h5cube.h5cube.cube_to_h5')
class TestCmdlineCompressGood(SuperCmdlineTest, ut.TestCase):
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
                    'ifac_s': ['-i', '-3e-2', '10', '-s'],
                    'mmax_s_nodec': ['-m', '-2e-2', '3e-1', '-s'],
                    'mmax_s_decnodig': ['-m', '-2.e-2', '3.e-1', '-s'],
                    'mmax_s_nodigdec': ['-m', '-.2e-1', '.3e0', '-s'],
                    'mmax_s_multidigdec': ['-m', '-200e-4', '30e-2', '-s'],
                    'mmax_s_cap_e': ['-m', '-2E-2', '3E-1', '-s']}

        # Return values
        kwdict = {'noargs': {'cubepath': scrfname,
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
                  'ifac_s': {'cubepath': scrfname,
                             'comp': None, 'trunc': None,
                             'thresh': True, 'delsrc': False,
                             'signed': True,
                             'isofactor': np.array([-0.03, 10.0])},
                  'mmax_s_nodec': {'cubepath': scrfname,
                                   'comp': None, 'trunc': None,
                                   'thresh': True, 'delsrc': False,
                                   'signed': True,
                                   'minmax': np.array([-2e-2, 3e-1])}}

        # Duplicate the mmax_s values to the other keys
        for k in [_ for _ in set(argsdict)
                  .symmetric_difference(set(kwdict.keys()))
                  if _.startswith('mmax_s_')]:
            kwdict.update({k: kwdict['mmax_s_nodec']})

        # Call the helper to do the tests
        self.good_test(baseargs, argsdict, kwdict, cth_mock)


@utm.patch('h5cube.h5cube.h5_to_cube')
class TestCmdlineDecompressGood(SuperCmdlineTest, ut.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()
        cls.copy_scratch('.h5cube', include=('grid20',))

    def setUp(self):
        self.store_args()

    def tearDown(self):
        self.restore_args()

    @classmethod
    def tearDownClass(cls):
        cls.clear_scratch()

    def test_CmdlineDecompress(self, htc_mock):
        from h5cube.h5cube import main as h5cube_main
        import numpy as np
        import sys

        # Arguments
        scrfname = self.scrfn('grid20.h5cube')
        baseargs = ['h5cube.py', scrfname]
        argsdict = {'noargs': [],
                    'delsrc': ['-d'],
                    'prec': ['-p', '4']}

        # Internal call values
        kwdict = {'noargs': {'h5path': scrfname, 'delsrc': False,
                             'prec': None},
                  'delsrc': {'h5path': scrfname, 'delsrc': True,
                             'prec': None},
                  'prec': {'h5path': scrfname, 'delsrc': False,
                           'prec': 4}}

        # Call the helper to do the tests
        self.good_test(baseargs, argsdict, kwdict, htc_mock)


def suite_cmdline_good():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestCmdlineCompressGood),
                tl.loadTestsFromTestCase(TestCmdlineDecompressGood)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

