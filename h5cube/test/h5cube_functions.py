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

    sizes_noargs = {'nt': {'grid20': 38876,
                           'grid25mo': 60151,
                           'grid20mo6-8': 89504},
                    'posix': {'grid20': 38856,
                              'grid25mo': 60641,
                              'grid20mo6-8': 90810}}
    sizes_t2 = {'nt': {'grid20': 28876,
                       'grid25mo': 40530,
                       'grid20mo6-8': 55860},
                'posix': {'grid20': 28584,
                          'grid25mo': 41037,
                          'grid20mo6-8': 57568}}
    sizes_m1e_8m10 = {'nt': {'grid20': 23989,
                             'grid25mo': 52313,
                             'grid20mo6-8': 80454},
                      'posix': {'grid20': 24243,
                                'grid25mo': 52798,
                                'grid20mo6-8': 82269}}
    sizes_i0x002f4 = {'nt': {'grid20': 17612,
                             'grid25mo': 26249,
                             'grid20mo6-8': 36446},
                      'posix': {'grid20': 17700,
                                'grid25mo': 26813,
                                'grid20mo6-8': 38458}}
    sizes_t8_i0x002f10 = {'nt': {'grid20': 19660,
                                 'grid25mo': 31995,
                                 'grid20mo6-8': 48114},
                          'posix': {'grid20': 18358,
                                    'grid25mo': 32573,
                                    'grid20mo6-8': 50049}}
    sizes_si0x002f5 = {'nt': {'grid20': 17612,
                              'grid25mo': 22138,
                              'grid20mo6-8': 27689},
                       'posix': {'grid20': 17592,
                                 'grid25mo': 22581,
                                 'grid20mo6-8': 28594}}

    fsize_delta = 20 # bytes filesize match window

    @staticmethod
    def shortsleep():
        from time import sleep
        sleep(0.1)

    @classmethod
    def ensure_scratch_dir(cls):
        import os

        # Ensure scratch directory exists
        if not os.path.isdir(cls.scrpath):
            os.mkdir(cls.scrpath)

    @classmethod
    def copy_scratch(cls):
        import os
        import shutil

        for fn in [fn for fn in os.listdir(cls.respath)
                   if fn.endswith('.cube')]:
            shutil.copy(os.path.join(cls.respath, fn),
                        os.path.join(cls.scrpath, fn))

        # To ensure filesystem caching &c. can catch up
        cls.shortsleep()

    @classmethod
    def clear_scratch(cls):
        import os

        for fn in os.listdir(cls.scrpath):
            os.remove(os.path.join(cls.scrpath, fn))

        # To ensure filesystem caching &c. can catch up
        cls.shortsleep()

    # Helper runner function
    @classmethod
    def runfxn(cls, fxn, ext, work_fn, orig_fn, msg, failobj=None, kwargs={}):
        # scrpath and fail should work ok late-bound. Bad practice in general!
        try:
            # Call indicated function with indicated work input file and
            # any kwargs passed
            fxn(cls.scrfn(work_fn + ext), **kwargs)

        except ValueError as e:
            # Compose the error message
            errmsg = "Unexpected exception on {0} ({1}): {2}".format(msg,
                                                                     orig_fn,
                                                                     str(e))
            try:
                # If a valid fail object is passed, call fail on it
                failobj.fail(msg=errmsg)
            except AttributeError:
                # Otherwise, just raise chained error
                raise ValueError(errmsg) from e

    # Helper scratch path/filename function
    @classmethod
    def scrfn(cls, fn):
        import os
        return os.path.join(cls.scrpath, fn)


class TestFunctionsCubeToH5_Good(SuperFunctionsTest, ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()

    def setUp(self):
        self.copy_scratch()

    def tearDown(self):
        self.clear_scratch()

    def basetest_FxnCubeToH5(self, sizes, **kwargs):
        """ Core cube_to_h5 test function"""
        import os
        from h5cube import cube_to_h5

        for fn in [fn for fn in os.listdir(self.scrpath)
                   if fn.endswith('.cube')]:
            # Should only capture files present at the start of fxn execution
            try:
                # Call with indicated extra arguments
                cube_to_h5(os.path.join(self.scrpath, fn), **kwargs)
            except Exception:
                self.fail(msg="Conversion failed on '{0}'".format(fn))

            h5path = os.path.splitext(fn)[0] + '.h5cube'
            h5path = os.path.join(self.scrpath, h5path)
            if hasattr(self, 'subTest'): # Needed since claiming py3.3 support
                with self.subTest(file=fn):
                    self.assertAlmostEqual(os.path.getsize(h5path),
                                           sizes[os.path.splitext(fn)[0]],
                                           delta=self.fsize_delta,  # bytes +/-
                                           msg="Unexpected filesize: {0}"
                                           .format(h5path))
            else:
                self.assertAlmostEqual(os.path.getsize(h5path),
                                       sizes[os.path.splitext(fn)[0]],
                                       delta=self.fsize_delta,  # bytes +/-
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

    @classmethod
    def setUpClass(cls):
        import os

        cls.longMessage = True
        cls.ensure_scratch_dir()

        # Set up the input and output paths
        cls.ifpath = os.path.join(cls.scrpath, 'grid20mo6-8.cube')
        cls.ofpath = os.path.join(cls.scrpath, 'mod.cube')

    def setUp(self):
        self.copy_scratch()

    def tearDown(self):
        self.clear_scratch()

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

        # Try running the conversion; should complain in the z-axis
        # import process because it's trying to parse the first geometry
        # line as the z-axis line
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

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

    def test_FxnCubeToH5_MissingYAXISVal(self):
        from h5cube import cube_to_h5

        # Hack off the last value
        self.copy_file_edit_line(4, delchars=9)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingZAXISVal(self):
        from h5cube import cube_to_h5

        # Hack off the last value
        self.copy_file_edit_line(5, delchars=9)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraXAXISVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(3, append="  0.30388")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraYAXISVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(4, append="  0.2627688")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraZAXISVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(5, append="  0.54886")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingGeomVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(8, delchars=9)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraGeomVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(8, append="  -0.398734")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingOrbVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(13, delchars=2)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraOrbVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(13, append="  12")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_MissingDataVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(18, delchars=13)

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)

    def test_FxnCubeToH5_ExtraDataVal(self):
        from h5cube import cube_to_h5

        # Append a new value to the last value
        self.copy_file_edit_line(22, append="  -4.2234E-13")

        # Conversion should fail
        self.assertRaises(ValueError, cube_to_h5, self.ofpath)


class TestFunctionsCycled(SuperFunctionsTest, ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()

    def setUp(self):
        self.copy_scratch()

    def tearDown(self):
        self.clear_scratch()

    def test_FxnCycled_2xCycle(self):
        from h5cube import cube_to_h5 as cth
        from h5cube import h5_to_cube as htc
        import os
        import shutil

        # Temp filename
        fn_cyc = 'cyc'

        # Test all of the files
        for fn in [s for s in os.listdir(self.scrpath) if s.endswith('.cube')]:
            # Copy the source file to the modified name
            shutil.copy(self.scrfn(fn), self.scrfn(fn_cyc + '.cube'))

            # Attempt first compression on the file, default options
            self.runfxn(cth, '.cube', fn_cyc, fn, 'initial compression',
                        failobj=self)

            # First decompression
            self.runfxn(htc, '.h5cube', fn_cyc, fn, 'initial decompression',
                        failobj=self)

            # Recompression
            self.runfxn(cth, '.cube', fn_cyc, fn, 'repeat compression',
                        failobj=self)

            # Re-decompression
            self.runfxn(htc, '.h5cube', fn_cyc, fn, 'repeat decompression',
                        failobj=self)


class TestFunctionsDataCheck(SuperFunctionsTest, ut.TestCase):
    from h5cube import H5

    # Working filenames
    fn1 = 'file1'
    fn2 = 'file2'

    # Log tolerance sought for LOGDATA match
    logtol = -9

    @classmethod
    def setUpClass(cls):
        from h5cube import cube_to_h5 as cth
        from h5cube import h5_to_cube as htc
        import os

        basefn = 'grid20mo6-8'
        cls.longMessage = True

        # Make sure scratch dir is present
        cls.ensure_scratch_dir()

        # Copy the resource files only once, before all tests run
        cls.copy_scratch()

        # Rename the multi-MO CUBE to first temp name
        os.rename(cls.scrfn(basefn + '.cube'), cls.scrfn(cls.fn1 + '.cube'))

        # First compression
        cls.runfxn(cth, '.cube', cls.fn1, basefn, 'first compression',
                   kwargs={'trunc': -cls.logtol})

        # First decompression
        cls.runfxn(htc, '.h5cube', cls.fn1, basefn, 'first decompression',
                   kwargs={'prec': -cls.logtol})

        # Rename the decompressed .cube to fn2
        os.rename(cls.scrfn(cls.fn1 + '.cube'), cls.scrfn(cls.fn2 + '.cube'))

        # Recompress
        cls.runfxn(cth, '.cube', cls.fn2, basefn, 'second compression',
                   kwargs={'trunc': -cls.logtol})

    @classmethod
    def tearDownClass(cls):
        # Clean up the scratch dir
        cls.clear_scratch()

    def do_h5py_test(self, key):
        import h5py as h5
        from h5cube import H5
        import numpy as np

        # Open the .h5cubes in a crash-safe way
        with h5.File(self.scrfn(self.fn1 + '.h5cube')) as hf1:
            with h5.File(self.scrfn(self.fn2 + '.h5cube')) as hf2:
                # First, ensure the key of interest is present
                self.assertIsNotNone(hf1.get(key))

                # try-except form of 'shape' membership testing, looking for
                # simple __eq__ comparables versus ndarrays
                try:
                    # If it has a shape member, assume it's an ndarray
                    hf1.get(key).value.shape
                except AttributeError:
                    # Probably not ndarray, just compare values
                    self.assertEqual(hf1.get(key).value, hf2.get(key).value)
                else:
                    # Probably is ndarray. Want same shape and identical values
                    self.assertEqual(hf1.get(key).value.shape,
                                     hf2.get(key).value.shape)

                    # LOGDATA doesn't always compare strictly equal.
                    if key == H5.LOGDATA:
                        self.assertTrue(np.isclose(hf1.get(key).value,
                                                   hf2.get(key).value,
                                                   atol=10. ** self.logtol)
                                        .all())
                    else:
                        self.assertTrue((hf1.get(key).value ==
                                         hf2.get(key).value).all())

    def test_FxnDataCheck_COMMENT1_Check(self):
        self.do_h5py_test(self.H5.COMMENT1)

    def test_FxnDataCheck_COMMENT2_Check(self):
        self.do_h5py_test(self.H5.COMMENT2)

    def test_FxnDataCheck_NUM_DSETS_Check(self):
        self.do_h5py_test(self.H5.NUM_DSETS)

    def test_FxnDataCheck_NATOMS_Check(self):
        self.do_h5py_test(self.H5.NATOMS)

    def test_FxnDataCheck_DSET_IDS_Check(self):
        self.do_h5py_test(self.H5.DSET_IDS)

    def test_FxnDataCheck_GEOM_Check(self):
        self.do_h5py_test(self.H5.GEOM)

    def test_FxnDataCheck_ORIGIN_Check(self):
        self.do_h5py_test(self.H5.ORIGIN)

    def test_FxnDataCheck_XAXIS_Check(self):
        self.do_h5py_test(self.H5.XAXIS)

    def test_FxnDataCheck_YAXIS_Check(self):
        self.do_h5py_test(self.H5.YAXIS)

    def test_FxnDataCheck_ZAXIS_Check(self):
        self.do_h5py_test(self.H5.ZAXIS)

    def test_FxnDataCheck_SIGNS_Check(self):
        self.do_h5py_test(self.H5.SIGNS)

    def test_FxnDataCheck_LOGDATA_Check(self):
        self.do_h5py_test(self.H5.LOGDATA)


def suite_misc():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc)])

    return s


def suite_goodh5():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Good)])

    return s


def suite_badh5():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Bad)])

    return s


def suite_cycledh5():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsCycled)])

    return s


def suite_datacheckh5():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsDataCheck)])

    return s


if __name__ == '__main__':  # pragma: no cover
    print("Module not executable.")

