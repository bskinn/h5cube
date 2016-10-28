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
        """ Mocked tests of 'success expected' compression operations """
        import numpy as np

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
        """ Mocked tests of 'success expected' decompression operations """
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


# Patch both so that they don't accidentally run.
@utm.patch('h5cube.h5cube.h5_to_cube')
@utm.patch('h5cube.h5cube.cube_to_h5')
class TestCmdlineBad(SuperCmdlineTest, ut.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()
        cls.copy_scratch('.cube', include=('grid20',))
        cls.copy_scratch('.h5cube', include=('grid20',))

    def setUp(self):
        self.store_args()

    def tearDown(self):
        self.restore_args()

    @classmethod
    def tearDownClass(cls):
        cls.clear_scratch()

    def run_nonparser_tests(self, ba, ad, rc):
        from h5cube.h5cube import main as h5cube_main
        import sys

        for name in ad:
            with self.subTest(name=name):
                # Spoof argv
                sys.argv = ba + ad[name]

                # Assert on the return code
                self.assertEqual(h5cube_main()[0], rc)


    def test_CmdlineParser(self, cth_mock, htc_mock):
        """ Tests of invalid cmdline input to be caught by argparse """
        from h5cube.h5cube import main as h5cube_main
        from h5cube import EXIT
        import sys

        # Arguments
        scrfname = self.scrfn('grid20.cube')
        baseargs = ['h5cube.py']
        argsdict = {'nofile': [],
                    'mult_posargs': [scrfname, 'abcde'],
                    'unk_optarg': [scrfname, '-q'],
                    'abs_signed': [scrfname, '-a', '-s'],
                    'abs_nothresh': [scrfname, '-a', '-n'],
                    'signed_nothresh': [scrfname, '-s', '-n'],
                    'comp_noval': [scrfname, '-c'],
                    'trunc_noval': [scrfname, '-t'],
                    'minmax_1val': [scrfname, '-m', '0.02'],
                    'isofac_1val': [scrfname, '-i', '0.002'],
                    'prec_noval': [scrfname, '-p'],
                    'mmax_and_isoval': [scrfname, '-m', '1e-5', '10',
                                        '-i', '0.002', '4']}

        # Run tests, expecting SystemExit
        for name in argsdict:
            with self.subTest(name=name):
                # Spoof argv
                sys.argv = baseargs + argsdict[name]

                # Call main(), expecting a SystemExit
                with self.assertRaises(SystemExit):
                    try:
                        h5cube_main()
                    except SystemExit as se:
                        # Catch, to check the exit code, then re-raise
                        self.assertEqual(EXIT.CMDLINE, se.code)
                        raise

    def test_CmdlineNonParserCMDLINE(self, cth_mock, htc_mock):
        """ Tests of invalid cmdline input not catchable by argparse """
        from h5cube import EXIT
        import shutil

        # Filenames & copying to 'no-good' extension
        scrcube = self.scrfn('grid20.cube')
        scrh5 = self.scrfn('grid20.h5cube')
        scrtxt = self.scrfn('test.txt')
        shutil.copy(scrcube, scrtxt)

        # Arguments
        baseargs = ['h5cube.py']
        argsdict = {'nothresh_minmax': [scrcube, '-n', '-m', '1e-4', '10'],
                    'nothresh_isofac': [scrcube, '-n', '-i', '0.002', '4'],
                    'comp_decomp': [scrcube, '-t', '5', '-p', '5'],
                    'mmax_wrong_order': [scrcube, '-m', '5', '2'],
                    'mmax_neg_min_in_abs': [scrcube, '-m', '-3', '5'],
                    'isof_zero_isovalue': [scrcube, '-i', '0.0', '5'],
                    'isof_fac_leq_one': [scrcube, '-i', '2e-3', '0.85'],
                    'isof_neg_iso_abs_mode': [scrcube, '-a', '-i', '-1e-2', '10'],
                    'abs_mode_no_vals': [scrcube, '-a'],
                    'sign_mode_no_vals': [scrcube, '-s'],
                    'comp_opt_to_h5': [scrh5, '-t', '4'],
                    'decomp_opt_to_cube': [scrcube, '-p', '6'],
                    'unk_file_ext': [scrtxt]}

        # Run tests, expecting an EXIT.CMDLINE exit code
        self.run_nonparser_tests(baseargs, argsdict, EXIT.CMDLINE)


    def test_CmdlineNonParserFILEREAD(self, cth_mock, htc_mock):
        """ Tests of file read errors not catchable by argparse """
        from h5cube import EXIT

        # Arguments
        baseargs = ['h5cube.py']
        argsdict = {'file_not_exist': ['notafile.cube']}

        # Run tests, expecting an EXIT.FILEREAD exit code
        self.run_nonparser_tests(baseargs, argsdict, EXIT.FILEREAD)


    def test_CmdlineNonParserInternalException(self, cth_mock, htc_mock):
        """ For when an error is thrown inside one of the API functions """

        from h5cube.h5cube import main as h5cube_main
        from h5cube import EXIT
        import sys

        # Spoof argv
        sys.argv = ['h5cube.py', self.scrfn('grid20.cube')]

        # Add a ValueError as a side-effect to the cth mock (has to be a
        # ValueError since that's what all of the data errors inside cth and htc
        # are thrown as)
        cth_mock.side_effect = ValueError("Dummy Exception")

        # Exit code should be a generic error for how the cth and htc
        # functions are currently set up.
        self.assertEqual(h5cube_main()[0], EXIT.GENERIC)

    def test_CmdlineErrorFormatter(self, cth_mock, htc_mock):
        """ Auxiliary test, to be sure the error formatter function works """

        from h5cube.h5cube import _error_format as _ef

        self.assertEqual(_ef(ValueError("abcd")), "ValueError: abcd")


def suite_cmdline_good():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestCmdlineCompressGood),
                tl.loadTestsFromTestCase(TestCmdlineDecompressGood)])

    return s


def suite_cmdline_bad():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestCmdlineBad)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

