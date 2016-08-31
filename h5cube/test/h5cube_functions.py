# ------------------------------------------------------------------------------
# Name:        h5cube_functions
# Purpose:     Tests for the (de)compression functionality
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


class TestFunctionsMisc(ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True

    def test_FxnMisc_ExpFormatGood(self):
        from h5cube.h5cube import _exp_format as _ef

        self.assertEqual(_ef(0.0183, 5), "  1.83000E-02")
        self.assertEqual(_ef(-11.2**99, 3), " -7.457E+103")
        self.assertEqual(_ef(2.853 * 3.122e-123, 6), "  8.907066E-123")

    def test_FxnMisc_ExpFormatBad(self):
        from h5cube.h5cube import _exp_format as _ef

        self.assertRaises(ValueError, _ef, "abcd", 5)
        self.assertRaises(TypeError, _ef, ValueError(), 2)


def suite():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc)])

    return s




if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

