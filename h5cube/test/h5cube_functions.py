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

    sizes_noargs = {'nt': {'grid20': 38180},
                    'posix': {'grid20': 38312}}
    sizes_t2 = {'nt': {'grid20': 28180},
                'posix': {'grid20': 28040}}
    sizes_m1e_8m10 = {'nt': {'grid20': 23685},
                      'posix': {'grid20': 23699}}
    sizes_i0x002f4 = {'nt': {'grid20': 17134},
                      'posix': {'grid20': 17156}}
    sizes_t8_i0x002f10 = {'nt': {'grid20': 18964},
                          'posix': {'grid20': 17814}}

    delta = 100 # bytes filesize match window

    @staticmethod
    def shortsleep():
        from time import sleep
        sleep(0.1)

    @classmethod
    def setUpClass(cls):
        import os

        cls.longMessage = True

        # Ensure scratch directory exists
        if not os.path.isdir(cls.scrpath):
            os.mkdir(cls.scrpath)

    def setUp(self):
        import os
        import shutil

        for fn in [fn for fn in os.listdir(self.respath)
                  if fn.endswith('.cube')]:
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

    def basetest_FxnCubeToH5(self, sizes, **kwargs):
        """ Core cube_to_h5 test function"""
        import os
        from h5cube import cube_to_h5

        for fn in [fn for fn in os.listdir(self.scrpath)
                   if fn.endswith('.cube')]:
            # Should only capture files present at the start of fxn execution
            try:
                # Call with indicated arguments
                cube_to_h5(os.path.join(self.scrpath, fn), **kwargs)
            except Exception:
                self.fail(msg="Conversion failed on '{0}'".format(fn))

            h5path = os.path.splitext(fn)[0] + '.h5cube'
            h5path = os.path.join(self.scrpath, h5path)
            self.assertAlmostEqual(os.path.getsize(h5path),
                                   sizes[os.path.splitext(fn)[0]],
                                   delta=self.delta, # bytes +/-
                                   msg="Unexpected filesize: {0}"
                                       .format(h5path))
            self.shortsleep() # Ensure filesystem is done working

    def test_FxnCubeToH5_NoArgs(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_noargs[os.name])

    def test_FxnCubeToH5_Trunc2(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_t2[os.name], trunc=2)

    def test_FxnCubeToH5_Minmax1e_8_10(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_m1e_8m10[os.name],
                                  thresh=True, minmax=[1e-8, 10])

    def test_FxnCubeToH5_Isofactor0x002_4(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_i0x002f4[os.name],
                                  thresh=True, isofactor=[0.002, 4])

    def test_FxnCubeToH5_Trunc8_Isofactor0x002_10(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_t8_i0x002f10[os.name],
                                  thresh=True, isofactor=[0.002, 10],
                                  trunc=8)

    def test_FxnCubeToH5_Delete(self):
        import os
        from h5cube import cube_to_h5

        fn = os.path.join(self.scrpath, "grid20.cube")

        # Extra confirmation that the file exists prior to processing
        self.assertTrue(os.path.isfile(fn))

        # Just test the one grid20.cube for post-compress deletion
        try:
            cube_to_h5(fn, delsrc=True)
        except Exception:
            self.fail(msg="Conversion failed on '{0}'".format(
                      fnbase + ".cube"))

        # Confirm source file was deleted
        self.assertFalse(os.path.isfile(fn))


def suite():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc),
                tl.loadTestsFromTestCase(TestFunctionsCubeToH5)])

    return s




if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

