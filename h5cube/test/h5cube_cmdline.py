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
        cls.copy_scratch('.cube', exclude=('grid25mo', 'grid20ang',
                                           'grid20mo6-8'))

    def setUp(self):
        self.store_args()

    def tearDown(self):
        self.restore_args()

    @classmethod
    def tearDownClass(cls):
        cls.clear_scratch()

    def test_CmdlineCompress(self, cth_mock):
        from h5cube.h5cube import main as h5cube_main
        import sys

        # Arguments
        argsdict = {'noargs': ['h5cube.py', self.scrfn('grid20.cube')],
                    'delsrc': ['h5cube.py', self.scrfn('grid20.cube'), '-d']}

        # Return values
        retsdict = {'noargs': {'cubepath': self.scrfn('grid20.cube'),
                               'comp': None, 'trunc': None,
                               'thresh': False, 'delsrc': False},
                    'delsrc': {'cubepath': self.scrfn('grid20.cube'),
                               'comp': None, 'trunc': None,
                               'thresh': False, 'delsrc': True}}

        for name in argsdict:
            with self.subTest(name=name):

                # Spoof argv
                sys.argv = argsdict[name]

                # Call the commandline main function
                h5cube_main()

                # Test the output
                cth_mock.assert_called_with(**retsdict[name])



def suite_cmdline_good():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestCmdlineCompressGood)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

