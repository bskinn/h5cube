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


class TestDummyTest(ut.TestCase):
    def test_DummyTest(self):
        self.assertEqual(1, 1)


def suite():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestDummyTest)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

