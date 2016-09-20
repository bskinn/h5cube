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


class SuperFunctionsTest(object):
    import os

    scrpath = os.path.join('h5cube', 'test', 'scratch')
    respath = os.path.join('h5cube', 'test', 'resource')

    sizes_noargs = {'nt': {'grid20': 38804,
                           'grid25mo': 60829,
                           'grid20mo6-8': 90973},
                    'posix': {'grid20': 38856,
                              'grid25mo': 60641,
                              'grid20mo6-8': 90810}}
    sizes_t2 = {'nt': {'grid20': 28804,
                       'grid25mo': 41168,
                       'grid20mo6-8': 57725},
                'posix': {'grid20': 28584,
                          'grid25mo': 41037,
                          'grid20mo6-8': 57568}}
    sizes_m1e_8m10 = {'nt': {'grid20': 24309,
                             'grid25mo': 52968,
                             'grid20mo6-8': 82420},
                      'posix': {'grid20': 24243,
                                'grid25mo': 52798,
                                'grid20mo6-8': 82269}}
    sizes_i0x002f4 = {'nt': {'grid20': 17854,
                             'grid25mo': 26982,
                             'grid20mo6-8': 38628},
                      'posix': {'grid20': 17700,
                                'grid25mo': 26813,
                                'grid20mo6-8': 38458}}
    sizes_t8_i0x002f10 = {'nt': {'grid20': 19588,
                                 'grid25mo': 32728,
                                 'grid20mo6-8': 50220},
                          'posix': {'grid20': 18358,
                                    'grid25mo': 32573,
                                    'grid20mo6-8': 50049}}
    sizes_si0x002f5 = {'nt': {'grid20': 17540,
                              'grid25mo': 22707,
                              'grid20mo6-8': 28767},
                       'posix': {'grid20': 17592,
                                 'grid25mo': 22581,
                                 'grid20mo6-8': 28594}}

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


class TestFunctionsCubeToH5_Good(SuperFunctionsTest, ut.TestCase):

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

    def test_FxnCubeToH5_SignedIsofactor0x002_5(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_si0x002f5[os.name],
                                  signed=True, thresh=True,
                                  isofactor=[0.002, 5])

    def test_FxnCubeToH5_NoneComp(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_noargs[os.name],
                                  comp=None)

    def test_FxnCubeToH5_NoneTrunc(self):
        import os
        self.basetest_FxnCubeToH5(sizes=self.sizes_noargs[os.name],
                                  trunc=None)

    def test_FxnCubeToH5_Clobber(self):
        import os

        # Just test the one grid20 cube, pre-writing the .h5cube to
        #  ensure clobbering works as expected
        fn = "grid20.h5cube"
        with open(os.path.join(self.scrpath, fn), 'w') as f:
            f.write('Dummy line of text\nAnother dummy line')

        self.basetest_FxnCubeToH5(sizes=self.sizes_noargs[os.name])

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
            self.fail(msg="Conversion failed on '{0}'".format(fn))

        # Confirm source file was deleted
        self.assertFalse(os.path.isfile(fn))


class TestFunctionsCubeToH5_Bad(SuperFunctionsTest, ut.TestCase):

    def __init__(self, *args, **kwargs):
        import os

        # These initializations go inside __init__ because access
        # to the superclass type 'scrpath' member is needed
        self.ifpath = os.path.join(self.scrpath, 'grid20.cube')
        self.ofpath = os.path.join(self.scrpath, 'mod.cube')

        # Call (implicitly) the TestCase __init__
        super().__init__(*args, **kwargs)

    def copy_file_remove_line(self, lnum):
        # Pull input contents
        with open(self.ifpath, 'r') as f:
            data = f.readlines()

        # Write everything but the target line
        with open(self.ofpath, 'w') as f:
            f.writelines(data[:lnum] + data[(lnum + 1):])

    def copy_file_edit_line(self, lnum, *, delchars=None, append=None):

        # Pull the input contents
        with open(self.ifpath, 'r') as f:
            data = f.readlines()

        # Remove characters if indicated
        if delchars:
            data[lnum] = data[lnum][:-(delchars + 1)] + '\n'

        # Append if indicated (must handle newline properly)
        if append:
            data[lnum] = data[lnum][:-1] + str(append) + '\n'

        # Write the edited file
        with open(self.ofpath, 'w') as f:
            f.writelines(data)

    def test_FxnCubeToH5_MissingComment(self):
        from h5cube import cube_to_h5

        # Remove the first line
        self.copy_file_remove_line(0)

        # Try running the conversion; should complain in the geometry import process
        # because it's trying to parse the first data line as the final geometry line
        self.assertRaises(IndexError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_StubNumatomsOriginLine(self):
        from h5cube import cube_to_h5

        # Stubify the numatoms line
        self.copy_file_edit_line(2, delchars=40)

        # Try the conversion; should throw a ValueError
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingOriginVal(self):
        from h5cube import cube_to_h5

        # Hack off the last origin value
        self.copy_file_edit_line(2, delchars=12)

        # Try running the conversion; should throw ValueError
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraOriginVal(self):
        from h5cube import cube_to_h5

        # Add an extra value
        self.copy_file_edit_line(2, append="  -0.03851")

        # Try running the conversion; should throw ValueError
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_SingleLineFile(self):
        from h5cube import cube_to_h5

        # Write the bad file
        with open(self.ofpath, 'w') as f:
            f.write('This is a single line in the file\n')

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingXAXISVal(self):
        from h5cube import cube_to_h5

        # Hack off the last value
        self.copy_file_edit_line(3, delchars=9)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)


def suite():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc),
                tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Good),
                tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Bad)])

    return s




if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

