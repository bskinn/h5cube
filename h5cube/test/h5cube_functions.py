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

    def test_FxnMisc_ExpFormat_Good(self):
        """ Validate correct scientific notation formatting for decompression """
        from h5cube.h5cube import _exp_format as _ef

        with self.subTest(type='typical'):
            self.assertEqual(_ef(0.0183, 5), "  1.83000E-02")

        with self.subTest(type='3-digit large'):
            self.assertEqual(_ef(-11.2**99, 3), " -7.457E+103")

        with self.subTest(type='3-digit small'):
            self.assertEqual(_ef(2.853 * 3.122e-123, 6), "  8.907066E-123")

    def test_FxnMisc_ExpFormat_Bad(self):
        """ Confirm _exp_format breaks when bad arguments are passed """
        from h5cube.h5cube import _exp_format as _ef

        with self.subTest(type='string'):
            self.assertRaises(ValueError, _ef, "abcd", 5)

        with self.subTest(type='object'):
            self.assertRaises(TypeError, _ef, ValueError(), 2)

    def test_FxnMisc_TryNext(self):
        """ Confirm _trynext works as expected """
        from h5cube.h5cube import _trynext

        with self.subTest(type='not_exhausted'):
            i = iter(range(5))
            next(i)
            next(i)
            self.assertEqual(_trynext(i, msg='Testing'), 2)

        with self.subTest(type='exhausted'):
            i = iter(range(2))
            next(i)
            next(i)
            self.assertRaises(ValueError, _trynext, i, msg='Testing')

    def test_FxnMisc_TryNoNext(self):
        """ Confirm _trynonext works as expected """
        from h5cube.h5cube import _trynonext

        with self.subTest(type='not_exhausted'):
            i = iter(range(3))
            next(i)
            self.assertRaises(ValueError, _trynonext, i, msg='Testing')

        with self.subTest(type='exhausted'):
            i = iter(range(2))
            next(i)
            next(i)
            try:
                _trynonext(i, 'Testing')
            except ValueError:
                self.fail()


class SuperFunctionsTest(object):
    import os

    scrpath = os.path.join('h5cube', 'test', 'scratch')
    respath = os.path.join('h5cube', 'test', 'resource')

    sizes_noargs = {'nt': {'grid20': 38876,
                           'grid20ang': 38876,
                           'grid25mo': 60151,
                           'grid20mo6-8': 89504,
                           'valtest': 17612},
                    'posix': {'grid20': 38928,
                              'grid20ang': 38928,
                              'grid25mo': 60098,
                              'grid20mo6-8': 89196,
                              'valtest': 17664}}
    sizes_t2 = {'nt': {'grid20': 28876,
                       'grid20ang': 28876,
                       'grid25mo': 40530,
                       'grid20mo6-8': 55860,
                       'valtest': 17612},
                'posix': {'grid20': 28584,
                          'grid20ang': 28584,
                          'grid25mo': 40582,
                          'grid20mo6-8': 55552,
                          'valtest': 17664}}
    sizes_m1e_8m10 = {'nt': {'grid20': 23989,
                             'grid20ang': 23989,
                             'grid25mo': 51871,
                             'grid20mo6-8': 79215,
                             'valtest': 17612},
                      'posix': {'grid20': 24041,
                                'grid20ang': 24041,
                                'grid25mo': 51659,
                                'grid20mo6-8': 79154,
                                'valtest': 17664}}
    sizes_i0x002f4 = {'nt': {'grid20': 17612,
                             'grid20ang': 17612,
                             'grid25mo': 25488,
                             'grid20mo6-8': 34610,
                             'valtest': 17612},
                      'posix': {'grid20': 17664,
                                'grid20ang': 17664,
                                'grid25mo': 25307,
                                'grid20mo6-8': 34440,
                                'valtest': 17664}}
    sizes_t8_i0x002f10 = {'nt': {'grid20': 19660,
                                 'grid20ang': 19660,
                                 'grid25mo': 30879,
                                 'grid20mo6-8': 46085,
                                 'valtest': 17612},
                          'posix': {'grid20': 18038,
                                    'grid20ang': 18038,
                                    'grid25mo': 30667,
                                    'grid20mo6-8': 45982,
                                    'valtest': 17664}}
    sizes_si0x002f5 = {'nt': {'grid20': 17612,
                              'grid20ang': 17612,
                              'grid25mo': 22138,
                              'grid20mo6-8': 27689,
                              'valtest': 17612},
                       'posix': {'grid20': 17664,
                                 'grid20ang': 17664,
                                 'grid25mo': 21929,
                                 'grid20mo6-8': 27516,
                                 'valtest': 17664}}

    # bytes filesize match window
    fsize_delta = 5000 if bool(os.environ.get('TOX')) else 20

    # Number of lines in the header of each file
    hdr_lines = {'grid20': 22,
                 'grid20ang': 22,
                 'grid25mo': 14,
                 'grid20mo6-8': 14,
                 'valtest': 8}

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

        # Ensure scratch directory is empty
        cls.clear_scratch()

    @classmethod
    def copy_scratch(cls, ext, *, include=(), exclude=()):
        import os
        import shutil

        for fn in [fn for fn in os.listdir(cls.respath)
                   if fn.endswith(ext)
                   and (not include or os.path.splitext(fn)[0] in include)
                   and not os.path.splitext(fn)[0] in exclude]:
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

    # Helper test method for things that could be ndarrays
    @staticmethod
    def robust_equal(v1, v2):
        try:
            # If it has a shape member, assume it's an ndarray
            v1.shape + v2.shape
        except AttributeError:
            # Probably not ndarray, just compare values. Will blow up if
            # one is ndarray and the other isn't
            return v1 == v2
        else:
            # Probably is ndarray. Want same shape and identical values
            return v1.shape == v2.shape and (v1 == v2).all()


class TestFunctionsCubeToH5_Good(SuperFunctionsTest, ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()

    def setUp(self):
        self.copy_scratch('.cube')

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
            with self.subTest(file=fn):
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

        fn = self.scrfn("grid20.cube")

        # Extra confirmation that the file exists prior to processing
        with self.subTest(type='exists_pre_exec'):
            self.assertTrue(os.path.isfile(fn))

        # Just test the one grid20.cube for post-compress deletion
        with self.subTest(type='during_compression'):
            try:
                cube_to_h5(fn, delsrc=True)
            except Exception:
                self.fail(msg="Conversion failed on '{0}'".format(fn))

        # Confirm source file was deleted
        with self.subTest(type='deleted_post_exec'):
            self.assertFalse(os.path.isfile(fn))

    def test_FxnCubeToH5_MultiLineOrbsList(self):
        """ Check that a multi-line orbital ID list compresses properly """
        import os

        # Filenames
        ifname = 'grid20mo6-8.cube'
        ofname = 'mod.cube'

        # Remove the non-interesting files
        [os.remove(self.scrfn(n)) for n in os.listdir(self.scrpath)
         if n != ifname]

        # Move the last orbital index to a new line. According to OpenBabel
        # implementation of CUBE import, this should read fine.
        with open(self.scrfn(ifname), 'r') as ifile:
            with open(self.scrfn(ofname), 'w') as ofile:
                for i, l in enumerate(ifile):
                    if i != 13:
                        ofile.write(l)
                    else:
                        ofile.write(l[:-2] + '\n')
                        ofile.write("    " + l[-2:]) # should include a newline

        # Remove the original file and rename the new to the old
        os.remove(self.scrfn(ifname))
        os.rename(self.scrfn(ofname), self.scrfn(ifname))

        # Try to process the output file (should be only the one left)
        self.basetest_FxnCubeToH5(sizes=self.sizes_noargs[os.name])

    def test_FxnCubeToH5_Thresholding(self):
        from h5cube import cube_to_h5 as cth
        from h5cube import H5
        import numpy as np
        import h5py as h5

        # Filename to work with; specially constructed cube for value testing
        cubefn = self.scrfn('valtest.cube')
        h5fn = self.scrfn('valtest.h5cube')

        # Dict of the extra args to pass
        argsdict={'nothresh': {},
                  'abs_val_nothresh': {'minmax': [1e-3, 1000],
                                     'thresh': True, 'signed': False,
                                     'clipzero': False},
                  'abs_val_hithresh': {'minmax': [1e-3, 50],
                                     'thresh': True, 'signed': False,
                                     'clipzero': False},
                  'abs_val_lothresh': {'minmax': [1e-1, 1000],
                                     'thresh': True, 'signed': False,
                                     'clipzero': False},
                  'abs_val_2xthresh': {'minmax': [1e-1, 30],
                                     'thresh': True, 'signed': False,
                                     'clipzero': False},
                  'sgn_val_posthresh': {'minmax': [1e-3, 25],
                                     'thresh': True, 'signed': True,
                                     'clipzero': False},
                  'sgn_val_negthresh': {'minmax': [-50, -1e-3],
                                        'thresh': True, 'signed': True,
                                        'clipzero': False},
                  'sgn_val_posneg': {'minmax': [-60, 40],
                                     'thresh': True, 'signed': True,
                                     'clipzero': False},
                  'abs_zero_nothresh': {'minmax': [1e-3, 1000],
                                        'thresh': True, 'signed': False,
                                        'clipzero': True},
                  'abs_zero_hithresh': {'minmax': [1e-3, 65],
                                        'thresh': True, 'signed': False,
                                        'clipzero': True},
                  'abs_zero_lothresh': {'minmax': [2e-1, 500],
                                        'thresh': True, 'signed': False,
                                        'clipzero': True},
                  'abs_zero_2xthresh': {'minmax': [2.5e-1, 74],
                                        'thresh': True, 'signed': False,
                                        'clipzero': True},
                  'sgn_zero_posthresh': {'minmax': [1.3e-3, 57],
                                         'thresh': True, 'signed': True,
                                         'clipzero': True},
                  'sgn_zero_negthresh': {'minmax': [-62, -4.8e-2],
                                         'thresh': True, 'signed': True,
                                         'clipzero': True},
                  'sgn_zero_posneg': {'minmax': [-32, 1.385e-4],
                                      'thresh': True, 'signed': True,
                                      'clipzero': True}}

        # Dict of the expected values in the compressed cube
        valsdict={'nothresh': np.array([-100, -0.01, 0, 0.01, 100]),
                  'abs_val_nothresh': np.array([-100, -0.01, 0.001, 0.01, 100]),
                  'abs_val_hithresh': np.array([-50, -0.01, 0.001, 0.01, 50]),
                  'abs_val_lothresh': np.array([-100, -0.1, 0.1, 0.1, 100]),
                  'abs_val_2xthresh': np.array([-30, -0.1, 0.1, 0.1, 30]),
                  'sgn_val_posthresh': np.array([1e-3, 1e-3, 1e-3, 0.01, 25]),
                  'sgn_val_negthresh': np.array([-50, -0.01, -1e-3,
                                                 -1e-3, -1e-3]),
                  'sgn_val_posneg': np.array([-60, -0.01, 0, 0.01, 40]),
                  'abs_zero_nothresh': np.array([-100, -0.01, 0, 0.01, 100]),
                  'abs_zero_hithresh': np.array([-65, -0.01, 0, 0.01, 65]),
                  'abs_zero_lothresh': np.array([-100, 0, 0, 0, 100]),
                  'abs_zero_2xthresh': np.array([-74, 0, 0, 0, 74]),
                  'sgn_zero_posthresh': np.array([0, 0, 0, 0.01, 57]),
                  'sgn_zero_negthresh': np.array([-62, 0, 0, 0, 0]),
                  'sgn_zero_posneg': np.array([-32, -0.01, 0,
                                               1.385e-4, 1.385e-4])}

        for name in argsdict:
            # Compress the test file with each set of indicated args
            cth(cubefn, **argsdict[name])

            # Open the h5cube and retrieve the values
            with h5.File(h5fn) as hf:
                vals = np.multiply(hf[H5.SIGNS],
                                   np.power(10, hf[H5.LOGDATA])).squeeze()

            # Check that the returned values match the expected ones
            with self.subTest(name=name):
                eqs = np.isclose(vals, valsdict[name], rtol=1e-4)
                eqmiss = np.nonzero(eqs == False)[0]
                valmiss = valsdict[name][eqmiss]
                retmiss = vals[eqmiss]
                self.assertTrue(np.all(eqs),
                                msg="(index, expected, actual) {0}"
                                    .format(list(zip(eqmiss,
                                                     valmiss, retmiss))))


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
        self.copy_scratch('.cube')

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
        """ Ensure ValueError thrown if natoms/origin line is truncated """
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


class TestFunctionsH5ToCube_Good(SuperFunctionsTest, ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()

    def setUp(self):
        self.copy_scratch('.h5cube')

    def tearDown(self):
        self.clear_scratch()

    @staticmethod
    def check_prec(fn, prec, lnum):
        import re

        p_prec = re.compile("-?\\d\.\\d{{{0}}}[ed]".format(prec), re.I)

        with open(fn, 'r') as f:
            lines = f.readlines()

        return p_prec.search(lines[lnum]) is not None

    def test_FxnH5ToCube_Prec(self):
        from h5cube import h5_to_cube as htc
        from h5cube import DEF
        import os

        prec_arg = [2, None]
        prec_expect = [2, DEF.PREC]

        for fn in os.listdir(self.scrpath):
            for pa, pe in zip(prec_arg, prec_expect):
                # Decompress
                htc(self.scrfn(fn), prec=pa)

                # Store the .cube filename
                cube_fn = os.path.splitext(fn)[0] + '.cube'

                # Store the line number to check
                lnum = self.hdr_lines[os.path.splitext(fn)[0]]

                with self.subTest(fn=fn, prec_arg=pa):
                    self.assertTrue(self.check_prec(self.scrfn(cube_fn), pe, lnum),
                                    msg="No value found with expected precision")

    def test_FxnH5ToCube_Delete(self):
        import os
        from h5cube import h5_to_cube as htc

        fn = self.scrfn("grid20.h5cube")

        # Extra confirmation that the file exists prior to processing
        with self.subTest(type='exists_pre_exec'):
            self.assertTrue(os.path.isfile(fn))

        # Just test the one grid20.cube for post-decompress deletion
        with self.subTest(type='during_decompression'):
            try:
                htc(fn, delsrc=True)
            except Exception:
                self.fail(msg="Conversion failed on '{0}'".format(fn))

        # Confirm source file was deleted
        with self.subTest(type='deleted_post_exec'):
            self.assertFalse(os.path.isfile(fn))


class TestFunctionsCycled(SuperFunctionsTest, ut.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True
        cls.ensure_scratch_dir()

    def setUp(self):
        self.copy_scratch('.cube')

    def tearDown(self):
        self.clear_scratch()

    def test_FxnCycled_2xCycle(self):
        """ Confirm no errors emerge on cycled compression/decompression """
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
        import os, shutil

        basefn = 'grid20mo6-8'
        cls.longMessage = True

        # Make sure scratch dir is present
        cls.ensure_scratch_dir()

        # Copy the resource files only once, before all tests run
        cls.copy_scratch('.cube')

        # Copy the multi-MO CUBE to first temp name
        shutil.copy(cls.scrfn(basefn + '.cube'), cls.scrfn(cls.fn1 + '.cube'))

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

    def test_FxnDataCheck_H5_Unified_Check(self):
        """ Confirm data consistency between a compressed and a re-compressed .h5cube """
        for key in [k for k in vars(self.H5)
                    if k == k.upper() and k == getattr(self.H5, k)]:
            with self.subTest(key=key):
                self.do_h5py_test(key)

    def test_FxnDataCheck_Cube_Header_Check(self):
        """ Confirm original and cycled .cubes have headers that parse to identical content """
        from h5cube import cube_to_h5 as cth
        from h5cube import h5_to_cube as htc
        from itertools import zip_longest as zipl
        import os

        for fn in [f for f in os.listdir(self.respath) if f.endswith('.cube')]:
            # Compress, rename, decompress
            old_fn = os.path.splitext(fn)[0] + 'old.cube'
            cth(self.scrfn(fn))
            os.rename(self.scrfn(fn), self.scrfn(old_fn))
            htc(self.scrfn(os.path.splitext(fn)[0] + '.h5cube'))

            # Open the .cubes and check the header contents
            with open(self.scrfn(fn), 'r') as newf:
                with open(self.scrfn(old_fn), 'r') as oldf:
                    # Comment lines
                    with self.subTest(fn=fn, type='comment1'):
                        self.assertEqual(next(newf), next(oldf))
                    with self.subTest(fn=fn, type='comment2'):
                        self.assertEqual(next(newf), next(oldf))

                    # Data lines
                    for i in range(self.hdr_lines[os.path.splitext(fn)[0]] - 2):
                        for j, t in enumerate(zipl(next(oldf).split(),
                                                   next(newf).split())):
                            with self.subTest(fn=fn, line=i, element=j):
                                self.assertEqual(t[0], t[1])


def suite_misc():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsMisc)])

    return s


def suite_goodcth():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Good)])

    return s


def suite_badcth():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsCubeToH5_Bad)])

    return s


def suite_goodhtc():
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestFunctionsH5ToCube_Good)])

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

