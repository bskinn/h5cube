# ------------------------------------------------------------------------------
# Name:        h5cube
# Purpose:     Script for h5py (de)compression of Gaussian CUBE files
#
# Author:      Brian Skinn
#                bskinn@alum.mit.edu
#
# Created:     20 Aug 2016
# Copyright:   (c) Brian Skinn 2016
# License:     The MIT License; see "LICENSE.txt" for full license terms
#                   and contributor agreement.
#
#       http://www.github.com/bskinn/h5cube
#
# ------------------------------------------------------------------------------

# Global imports
import sys

# Argparse constants
class AP(object):
    PATH = 'path'
    DELETE = 'delete'
    COMPRESS = 'compress'
    TRUNC = 'truncate'
    PREC = 'precision'
    ABSMODE = 'absolute'
    SIGNMODE = 'signed'
    NOTHRESH = 'nothresh'
    MINMAX = 'minmax'
    ISOFACTOR = 'isofactor'

# h5py constants
class H5(object):
    COMMENT1 = 'COMMENT1'
    COMMENT2 = 'COMMENT2'
    NATOMS = 'NATOMS'
    ORIGIN = 'ORIGIN'
    XAXIS = 'XAXIS'
    YAXIS = 'YAXIS'
    ZAXIS = 'ZAXIS'
    GEOM = 'GEOM'
    NUM_DSETS = 'NUM_DSETS'
    DSET_IDS = 'DSET_IDS'
    SIGNS = 'SIGNS'
    LOGDATA = 'LOGDATA'

    VAL_NOT_ORBFILE = 0

# Default values
class DEF(object):
    TRUNC = 5
    PREC = 5
    COMP = 9
    DEL = False
    THRESH = False

# Exit codes
class EXIT(object):
    OK = 0
    GENERIC = 1
    CMDLINE = 2
    FILEREAD = 4
    FILEWRITE = 8

def _exp_format(val, prec):
    """ [Docstring]

    """

    # Convert val using string formatting: Always a leading space;
    # positive values with another leading space; negatives with the negative
    # sign; one digit in front of the decimal, 'dec' digits after.
    # Capital 'E' for the exponent.
    out = " {{: #1.{0}E}}".format(prec).format(val)

    # Return the results
    return out

def _trynext(iterator, msg):
    """ [Docstring]

    """

    try:
        retval = next(iterator)
    except StopIteration as e:
        raise ValueError("Data prematurely exhausted in '{0}' dataset"
                         .format(msg)) from e

    return retval

def _trynonext(iterator, msg):
    """ [Docstring]

    """

    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise ValueError("Superfluous values in '{0}' dataset".format(msg))


def cube_to_h5(cubepath, *, delsrc=DEF.DEL, comp=DEF.COMP, trunc=DEF.TRUNC,
               thresh=DEF.THRESH, signed=None, minmax=None, isofactor=None):
    """ [Docstring]

    """

    import h5py as h5
    import itertools as itt
    import numpy as np
    import os
    import re

    # Default compression and truncations, if no value(s) passed on commandline
    if comp is None:
        comp = DEF.COMP
    if trunc is None:
        trunc = DEF.TRUNC

    # Pull the file contents and make an iterator
    with open(cubepath) as f:
        filedata = f.read()
    datalines = iter(filedata.splitlines())

    # Construct the .h5cube path
    h5path = os.path.splitext(cubepath)[0] + '.h5cube'

    # Clobber to new file
    if os.path.isfile(h5path):
        os.remove(h5path)

    # Context manager for the h5py file
    with h5.File(h5path) as hf:

        # === COMMENT# Lines ===
        hf.create_dataset(H5.COMMENT1, data=_trynext(datalines, H5.COMMENT1))
        hf.create_dataset(H5.COMMENT2, data=_trynext(datalines, H5.COMMENT2))

        # === NATOMS and ORIGIN ===
        elements = iter(_trynext(datalines, H5.ORIGIN).split())

        # Store number of atoms; can be negative to indicate an orbital
        # CUBE
        natoms = int(_trynext(elements, H5.NATOMS))
        hf.create_dataset(H5.NATOMS, data=natoms)
        is_orbfile = (natoms < 0)
        natoms = abs(natoms)

        # Try storing the origin, complaining if not enough data
        hf.create_dataset(H5.ORIGIN,
                          data=np.array([float(_trynext(elements, H5.ORIGIN))
                                         for _ in range(3)]))

        # Complain if too much data
        _trynonext(elements, H5.ORIGIN)

        # === SYSTEM AXES ===
        # Dimensions and vectors
        #
        # Dimensions can be negative to indicate Angstrom units; the
        #  data implications don't really matter, just the absolute value
        #  needs to be used for sizing the data array.
        dims = []
        for dsname in [H5.XAXIS, H5.YAXIS, H5.ZAXIS]:
            elements = iter(_trynext(datalines, dsname).split())
            hf.create_dataset(dsname,
                              data=np.array([float(_trynext(elements, dsname))
                                             for _ in range(4)]))
            dims.append(abs(int(hf[dsname].value[0])))
            _trynonext(elements, dsname)

        # === GEOMETRY ===
        # Expect |NATOMS| lines with atom & geom data
        geom = np.zeros((natoms, 5))
        for i in range(natoms):
            elements = iter(_trynext(datalines, H5.GEOM).split())
            for j in range(5):
                geom[i, j] = _trynext(elements, H5.GEOM)
            _trynonext(elements, H5.GEOM)

        hf.create_dataset(H5.GEOM, data=geom)

        # === ORBITAL INFO LINE ===
        # (only present if natoms < 0)
        if is_orbfile:
            # Get iterator for the next line
            elements = iter(_trynext(datalines, H5.DSET_IDS).split())

            # Pull the number of datasets and store
            num_dsets = int(_trynext(elements, H5.NUM_DSETS))
            hf.create_dataset(H5.NUM_DSETS, data=num_dsets)

            # Try to retrieve num_dsets values for the orbital indices;
            #  complain if not enough, or if too many, and write the dataset
            # Initialize the container
            dset_ids = []

            # Loop while more values expected
            while len(dset_ids) < num_dsets:
                try:
                    # Try appending the next value in the iterator
                    dset_ids.append(int(next(elements)))
                except StopIteration:
                    # Ran out of values. Pull the next line.
                    elements = iter(_trynext(datalines, H5.DSET_IDS).split())
                except ValueError as e:
                    # Catch a non-integer value, for the case where there
                    # aren't enough dataset ID values and parsing
                    # erroneously moves to data values.
                    raise ValueError(
                        "Data prematurely exhausted in '{0}' dataset"
                        .format(H5.DSET_IDS)) from e

            # Make sure the most recent line was fully exhausted.
            _trynonext(elements, H5.DSET_IDS)

            # Store the dataset
            hf.create_dataset(H5.DSET_IDS, data=dset_ids)

            # Extend the dimensions array with the number of datasets
            dims.append(num_dsets)

        else:
            # Not an orbfile
            hf.create_dataset(H5.NUM_DSETS, data=H5.VAL_NOT_ORBFILE)
            hf.create_dataset(H5.DSET_IDS, data=np.array([]))

        # === VOLUMETRIC FIELD DATA ===

        # Regex pattern for lines of scientific notation
        p_scinot = re.compile("""
            -?                           # Optional leading negative sign
            \\d                          # Single leading digit
            \\.                          # Decimal point
            \\d*                         # Digits (could be none, zero precision)
            [de]                         # Accept either 0.000d00 or 0.000e00
            [+-]                         # Sign of the exponent
            \\d+                         # Digits of the exponent
            """, re.X | re.I)

        # Agglomerated iterator for all remaining data in file
        dataiter = itt.chain.from_iterable(p_scinot.finditer(l)
                                           for l in datalines)

        # Preassign the calculated minmax values if isofactored thresh
        # is enabled
        if thresh and isofactor is not None:
            # Populate minmax with the isovalue/factor based
            # threshold values
            minmax = np.zeros((2,))
            minmax[0] = isofactor[0] / isofactor[1]
            minmax[1] = isofactor[0] * isofactor[1]

        # Fill the working numpy object, chaining a more informative exception
        # if the data pull fails
        try:
            workdataarr = np.array(list(map(lambda s: np.float(s.group(0)),
                                            dataiter))).reshape(dims)
        except ValueError as e:
            raise ValueError('Error parsing volumetric data') from e

        # Store the signs for output
        signsarr = np.sign(workdataarr).astype(np.int8)

        # Adjusted working log values; zeroes substituted with ones
        np.add(workdataarr, 1.0 - np.abs(signsarr), out=workdataarr)

        # Threshold. Spread out the np calls for easier reading, and calculate
        # in-place for reduced RAM usage.
        if thresh:
            if signed:
                # Threshold, then absval
                np.clip(workdataarr, *minmax, out=workdataarr)
                np.abs(workdataarr, out=workdataarr)
            else:
                # Absval, then threshold
                np.abs(workdataarr, out=workdataarr)
                np.clip(workdataarr, *minmax, out=workdataarr)
        else:
            # Just absval if no thresholding
            np.abs(workdataarr, out=workdataarr)

        # Finish with log base 10
        np.log10(workdataarr, out=workdataarr)

        # Store the arrays, compressed (implicitly activates auto-sized
        #  chunking)
        hf.create_dataset(H5.LOGDATA, data=workdataarr, compression="gzip",
                          compression_opts=comp, shuffle=True, scaleoffset=trunc)
        hf.create_dataset(H5.SIGNS, data=signsarr, compression="gzip",
                          compression_opts=comp, shuffle=True, scaleoffset=0)

    # If indicated, delete the source file
    if delsrc:
        os.remove(cubepath)


def h5_to_cube(h5path, *, delsrc=DEF.DEL, prec=DEF.PREC):
    """ [Docstring]

    Less error/syntax checking here since presumably the data was
    parsed for validity when the .h5cube file was created.
    """

    import h5py as h5
    import itertools as itt
    import numpy as np
    import os

    # Default precision value, if no value passed on commandline
    if prec is None:
        prec = DEF.PREC

    # Define the header block substitution strings
    hdr_3val = "{:5d}   {: 1.6f}   {: 1.6f}   {: 1.6f}"
    hdr_4val = "{:5d}   {: 1.6f}   {: 1.6f}   {: 1.6f}   {: 1.6f}"
    hdr_orbinfo = "   {:d}"

    # Define the uncompressed filename
    cubepath = os.path.splitext(h5path)[0] + '.cube'

    # Open the source file
    with h5.File(h5path) as hf:

        # Delete any existing output file
        if os.path.isfile(cubepath):
            os.remove(cubepath)

        # Open the output file for writing as a context manager
        with open(cubepath, 'w') as f:
            # Write the two comment lines
            f.write(hf[H5.COMMENT1].value + '\n')
            f.write(hf[H5.COMMENT2].value + '\n')

            # Write the number-of-atoms and system origin line
            # Number of atoms could be negative; want to retain the negative
            # value in the output but convert the number of atoms value to be
            # positive.
            natoms = hf[H5.NATOMS].value
            f.write(hdr_3val.format(natoms, *(hf[H5.ORIGIN].value)) + '\n')
            is_orbfile = (natoms < 0)
            if is_orbfile:
                natoms = abs(natoms)

            # Write the three axes lines
            dims = []
            for dsname in [H5.XAXIS, H5.YAXIS, H5.ZAXIS]:
                ds = hf[dsname].value
                f.write(hdr_3val.format(int(ds[0]), *ds[1:]) + '\n')
                dims.append(abs(int(ds[0]))) # values could be negative

            # Write the geometry
            geom = hf[H5.GEOM].value
            for i in range(natoms):
                f.write(hdr_4val.format(int(geom[i,0]), *geom[i,1:]) + '\n')

            # If an orbital file, write the orbital info line and append the
            # number of datasets to the 'dims' variable
            if is_orbfile:
                # Store the dataset dimension
                dims.append(int(hf[H5.NUM_DSETS].value))

                # Write the dataset dimension to the output
                f.write(hdr_orbinfo.format(dims[-1]))

                # Write all of the orbital dataset IDs to output.
                for i, v in enumerate(hf[H5.DSET_IDS].value):
                    # Write the formatted value (mostly just adding spaces)
                    f.write(hdr_orbinfo.format(int(v)))

                    # Write at most six entries per line; always include
                    # an EOL after the final value
                    if i % 6 == 4 or i == dims[-1] - 1:
                        f.write('\n')

            # Write the data blocks
            # Pull them from the .h5cube file first
            # Value-by-value data retrieval was tried and found to be
            #  HORRIFICALLY slow. Chunk-by-chunk retrieval might be better
            #  speed-wise, but appears to decrease the .h5cube compression
            #  factor by at least two-fold.
            signs = hf[H5.SIGNS].value
            logvals = hf[H5.LOGDATA].value
            outvals = np.multiply(signs, 10.0**logvals)

            # Can just run a combinatorial iterator over the dimensions
            # of the dataset
            for i, t in enumerate(itt.product(*map(range, dims))):
                # f.write(_exp_format(hf[H5.SIGNS].value[t] *
                #                     10.**hf[H5.LOGDATA].value[t], prec))
                # f.write(_exp_format(signs[t] * 10. ** logvals[t], prec))
                f.write(_exp_format(outvals[t], prec))

                # Newline to wrap at a max of six values per line, or if at
                # the last entry of a z-iteration and at the last dataset,
                # for orbital files.
                if i % 6 == 5 or (t[2] == dims[2] - 1 and
                                  t[-1] == dims[-1] - 1):
                    f.write('\n')

            # Always newlines at end
            f.write('\n\n')

    # If indicated, delete the source file
    if delsrc:
        os.remove(h5path)


def _validate_minmax(minmax, signed):
    """ [Docstring]

    """

    if minmax[0] >= minmax[1]:
        return (False, "Error: 'max' is not greater than 'min'")

    if not signed and minmax[0] < 0:
        return (False, "Error: Negative 'min' in absolute "
                       "thresholding mode")

    return (True, "")


def _validate_isofactor(isofactor, signed):
    """ [Docstring]

    """

    if isofactor[0] == 0.0:
        return (False, "Error: 'isovalue' cannot be zero")

    if isofactor[1] <= 1.0:
        return (False, "Error: 'factor' must be greater than one")

    if not signed and isofactor[0] < 0:
        return (False, "Error: Negative 'isovalue' in absolute "
                       "thresholding mode")

    return (True, "")


def _error_format(e):
    """ [Docstring]

    """

    import re
    name = re.compile("'([^']+)'").search(str(e.__class__)).group(1)
    return "{0}: {1}".format(name, " - ".join(e.args))


def _run_fxn_errcatch(fxn, **kwargs):

    try:
        fxn(**kwargs)
    except Exception as e:
        return (EXIT.GENERIC, _error_format(e))
    else:
        return (EXIT.OK, "")


def _get_parser():
    """ [Docstring]

    """

    import argparse as ap

    # Core parser
    prs = ap.ArgumentParser(description="Gaussian CUBE (de)compression "
                                        "via h5py",
                            epilog="Bugs can be reported at "
                                   "https://github.com/bskinn/h5cube/issues. "
                                   "Documentation can be found at "
                                   "http://h5cube.readthedocs.io.")

    # Compression group
    gp_comp = prs.add_argument_group(title="compression options")

    # Thresholding "subgroups" within compression
    gp_threshmode = prs.add_argument_group(title="compression thresholding "
                                                 "mode (mutually exclusive)")
    gp_threshvals = prs.add_argument_group(title="compression thresholding "
                                                 "values (mutually exclusive)")

    # Decompression group
    gp_decomp = prs.add_argument_group(title="decompression options")



    # Mutually exclusive subgroups for the compression operation
    meg_threshmode = gp_threshmode.add_mutually_exclusive_group()
    meg_threshvals = gp_threshvals.add_mutually_exclusive_group()

    # Argument for the filename (core parser)
    prs.add_argument(AP.PATH, action='store',
                     help="path to file to be (de)compressed, where "
                          "the operation to be performed is hard coded based "
                          "on the file extension: .cub/.cube files are "
                          "compressed to .h5cube, .h5cube files are "
                          "decompressed to .cube, and "
                          "the program exits with an error "
                          "on any other extension")

    # Argument to delete the source file; default is to keep (core)
    prs.add_argument('-{0}'.format(AP.DELETE[0]), '--{0}'.format(AP.DELETE),
                     action='store_true',
                     help="delete the source file after (de)compression")

    # gzip compression level (compress)
    gp_comp.add_argument('-{0}'.format(AP.COMPRESS[0]),
                         '--{0}'.format(AP.COMPRESS),
                         action='store', default=None, type=int,
                         choices=list(range(10)),
                         metavar='#',
                         help="gzip compression level for volumetric "
                              "data (0-9, default {0})".format(DEF.COMP))

    # gzip truncation level (compress)
    gp_comp.add_argument('-{0}'.format(AP.TRUNC[0]),
                         '--{0}'.format(AP.TRUNC),
                         action='store', default=None, type=int,
                         choices=list(range(16)),
                         metavar='#',
                         help="h5py scale-offset filter truncation width "
                              "for volumetric "
                              "data (number of mantissa digits retained; "
                              "0-15, default {0})".format(DEF.TRUNC))

    # Absolute thresholding mode (compress -- threshold mode)
    meg_threshmode.add_argument('-{0}'.format(AP.ABSMODE[0]),
                                '--{0}'.format(AP.ABSMODE),
                                action='store_true',
                                help="absolute-value thresholding "
                                     "mode (default if -{0} or -{1} "
                                     "specified".format(AP.MINMAX[0],
                                     AP.ISOFACTOR[0]))

    # Signed thresholding mode (compress -- threshold mode)
    meg_threshmode.add_argument('-{0}'.format(AP.SIGNMODE[0]),
                                '--{0}'.format(AP.SIGNMODE),
                                action='store_true',
                                help="signed-value thresholding "
                                     "mode")

    # Thresholding mode disabled (compress -- threshold mode)
    meg_threshmode.add_argument('-{0}'.format(AP.NOTHRESH[0]),
                                '--{0}'.format(AP.NOTHRESH),
                                action='store_true',
                                help="thresholding disabled (default)")


    # Min/max threshold specification (compress -- threshold values)
    meg_threshvals.add_argument('-{0}'.format(AP.MINMAX[0]),
                                '--{0}'.format(AP.MINMAX),
                                action='store',
                                default=None,
                                nargs=2,
                                metavar='#',
                                help="min and max values for "
                                     "threshold specification (provide as "
                                     "-m [min] [max])")

    # Isovalue/factor threshold specification (compress -- threshold values)
    meg_threshvals.add_argument('-{0}'.format(AP.ISOFACTOR[0]),
                                '--{0}'.format(AP.ISOFACTOR),
                                action='store',
                                default=None,
                                nargs=2,
                                metavar='#',
                                help="Isovalue and multiplicative "
                                     "factor values for "
                                     "threshold specification (e.g., "
                                     "'-i 0.002 4' corresponds to "
                                     "'-m 0.0005 0.008')")

    # Data block output precision (decompress)
    gp_decomp.add_argument('-{0}'.format(AP.PREC[0]),
                           '--{0}'.format(AP.PREC),
                           action='store', default=None, type=int,
                           choices=list(range(16)),
                           metavar='#',
                           help="volumetric data block output "
                                "precision (0-15, "
                                "default {0})".format(DEF.PREC))
    return prs


def _tweak_neg_scinot():
    """ [Docstring]

    Modification of http://stackoverflow.com/a/21446783/4376000

    """
    import re
    p = re.compile('-\\d*\\.?\\d*e', re.I)
    sys.argv = [' ' + a if p.match(a) else a for a in sys.argv]


def main():

    import numpy as np
    import os

    # Retrieve the argument parser
    prs = _get_parser()

    # Preprocess the arguments to avoid confusing argparse with any
    # negative values in scientific notation.
    _tweak_neg_scinot()

    # Parse known args, convert to dict, and leave unknown args in sys.argv
    ns, args_left = prs.parse_known_args()
    params = vars(ns)
    sys.argv = sys.argv[:1] + args_left

    # Retrieve path and file extension
    path = params[AP.PATH]
    ext = os.path.splitext(path)[1]

    # Check for existence
    if not os.path.isfile(path):
        return (EXIT.FILEREAD, "Error: File not found.")

    # Retrieve other parameters
    delsrc = params[AP.DELETE]
    comp = params[AP.COMPRESS]
    trunc = params[AP.TRUNC]
    prec = params[AP.PREC]
    absolute = params[AP.ABSMODE]
    signed = params[AP.SIGNMODE]
    nothresh = params[AP.NOTHRESH]
    minmax = params[AP.MINMAX]
    isofactor = params[AP.ISOFACTOR]

    # Composite indicators for which types of arguments passed
    def not_none_or_false(x):
        # Want False return ONLY if x *is* None or x *is* False.
        # Numerical 'falsey' values in particular should lead to
        # a True return.
        return x is not None and x is not False

    compargs = any(map(not_none_or_false, [comp, trunc, absolute,
                                           signed, nothresh,
                                           minmax, isofactor]))

    decompargs = any(map(not_none_or_false, [prec]))

    # Complain if nothresh specified but minmax or isofactor provided
    if nothresh and not (minmax is None and isofactor is None):
        return (EXIT.CMDLINE, "Error: Thresholding parameter specified"
                              "with --nothresh")

    # Complain if compression and decompression arguments mixed
    if compargs and decompargs:
        return (EXIT.CMDLINE, "Error: Both compression and decompression"
                              "options specified")

    # Convert and validate the thresholding inputs
    if minmax is not None:
        minmax = np.float_(minmax)
        out = _validate_minmax(minmax, signed)
        if not out[0]:
            return (EXIT.CMDLINE, out[1])

    if isofactor is not None:
        isofactor = np.float_(isofactor)
        out = _validate_isofactor(isofactor, signed)
        if not out[0]:
            return (EXIT.CMDLINE, out[1])

    # Complain if a thresholding mode is indicated but no
    # threshold values are provided
    if (absolute or signed) and (minmax is None and isofactor is None):
        return (EXIT.CMDLINE, "Error: Thresholding mode specified but"
                              "no values provided")

    # Check file extension as indication of execution mode
    if ext.lower() == '.h5cube':
        # Decompression mode
        if compargs:
            return (EXIT.CMDLINE, "Error: compression arguments passed to "
                                  "decompression operation")

        return _run_fxn_errcatch(h5_to_cube, h5path=path, delsrc=delsrc,
                                 prec=prec)

    elif ext.lower() in ['.cube', '.cub']:
        # Compression mode
        if decompargs:
            return (EXIT.CMDLINE, "Error: decompression arguments passed to "
                                 "compression operation")

        if minmax is not None:
            # Min/max thresholding
            return _run_fxn_errcatch(cube_to_h5, cubepath=path, delsrc=delsrc,
                                     comp=comp, trunc=trunc, thresh=True,
                                     signed=signed, minmax=minmax)

        elif isofactor is not None:
            # Isovalue thresholding
            return _run_fxn_errcatch(cube_to_h5, cubepath=path, delsrc=delsrc,
                                     comp=comp, trunc=trunc, thresh=True,
                                     signed=signed, isofactor=isofactor)

        else:
            # No thresholding
            return _run_fxn_errcatch(cube_to_h5, cubepath=path, thresh=False,
                                     delsrc=delsrc, comp=comp, trunc=trunc)

    else:
        return (EXIT.CMDLINE, "Error: File extension not recognized.")


def script_run():   # pragma: no cover
    # Run program
    out = main()

    # If a message, print it
    if out[1]:
        print(out[1])

    # Exit with whatever code
    sys.exit(out[0])

if __name__ == '__main__':   # pragma: no cover
    script_run()

