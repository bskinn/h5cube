# ------------------------------------------------------------------------------
# Name:        h5cube_functions
# Purpose:     Tests for the API functions
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


class TestFunctionsCubeToH5(ut.TestCase):
    import os

    scrpath = os.path.join('h5cube', 'test', 'scratch')
    respath = os.path.join('h5cube', 'test', 'resource')

    names = {'grid20'}
    sizes_noargs = {'grid20': 38180}

    delta = 100 # bytes filesize match window

    @staticmethod
    def shortsleep():
        from time import sleep
        sleep(0.1)

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True

    def setUp(self):
        import os
        import shutil

        for fn in [fn for fn in os.listdir(self.respath)
                  if fn.endswith('.cube')]:
            print(fn)
            shutil.copy(os.path.join(self.respath, fn),
                        os.path.join(self.scrpath, fn))

        # To ensure filesystem caching &c. can catch up
        self.shortsleep()

    def tearDown(self):
        import os

        for fn in os.listdir(self.scrpath):
            os.remove(os.path.join(self.scrpath, fn))

        # To ensure filesystem caching &c. can catch up
        self.shortsleep()

    def test_FxnCubeToH5_NoArgs(self):
        import os
        from h5cube import cube_to_h5

        for fn in [fn for fn in os.listdir(self.scrpath)
                   if fn.endswith('.cube')]:
            # Should only capture files present at the start of fxn execution
            try:
                # Call with all defaults
                cube_to_h5(os.path.join(self.scrpath, fn))
            except Exception:
                self.fail("Conversion failed on '{0}'".format(fn))

            h5path = os.path.splitext(fn)[0] + '.h5cube'
            h5path = os.path.join(self.scrpath, h5path)
            self.assertAlmostEqual(os.path.getsize(h5path),
                                   self.sizes_noargs[os.path.splitext(fn)[0]],
                                   delta=self.delta, # bytes +/-
                                   msg="Unexpected filesize: {0}"
                                       .format(h5path))
            self.shortsleep()


def suite():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc),
                tl.loadTestsFromTestCase(TestFunctionsCubeToH5)])

    return s




if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

