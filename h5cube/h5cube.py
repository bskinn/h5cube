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

# def _convertval(val, signed, thresh, minmax):
#     """ [Docstring]
#
#     """
#
#     import numpy as np
#
#     # Min <= Max is required. Can't imagine a use-case for equal min and max
#     # at the moment, but may be desired by someone at some point?
#     if thresh and minmax is not None and minmax[0] > minmax[1]:
#         raise ValueError('min <= max is required')
#
#     # If using unsigned thresholding, both min and max have to be non-negative
#     if thresh and (not signed) and minmax is not None and \
#                                                 np.any(np.array(minmax) < 0):
#         raise ValueError('0 <= min <= max required for unsigned thresholding')
#
#     # Threshold, if indicated
#     if thresh:
#         if signed:
#             if val < minmax[0]:
#                 val = minmax[0]
#             elif val > minmax[1]:
#                 val = minmax[1]
#         else:
#             if np.abs(val) < minmax[0]:
#                 val = (np.sign(val) if val else 1.0) * minmax[0]
#             elif np.abs(val) > minmax[1]:
#                 val = np.sign(val) * minmax[1]
#
#     # Special return value for zero; otherwise calculate the separate
#     # values for the sign of the value and the base-10 logarithm of its
#     # absolute value.
#     if val == 0.0:
#         return [0.0, 0.0]
#     else:
#         return [np.sign(val), np.log10(np.abs(val))]


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
                    # Catch a non-integer value, for the case where there \
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

        # Volumetric field data
        # Create one big iterator over a scientific notation regular
        #  expression for the remainder of the file

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

        # Fill the working numpy object
        workdataarr = np.array(list(map(lambda s: np.float(s.group(0)),
                                        dataiter))).reshape(dims)

        # Store the signs for output
        signsarr = np.sign(workdataarr).astype(np.int8)

        # Initial framework for low-RAM vs faster implementation
        # if lowmem:
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

        # else:
        #     # Adjusted working log values; zeroes substituted with ones
        #     workdataarr = workdataarr + (1.0 - np.sign(np.abs(workdataarr)))
        #
        #     # Threshold, if indicated, and calculate log10(abs(..))
        #     if thresh:
        #         if signed:
        #             # Threshold, then absval
        #             workdataarr = np.log10(np.abs(np.clip(workdataarr, *minmax)))
        #
        #         else:
        #             # Absval, then threshold
        #             workdataarr = np.log10(np.clip(np.abs(workdataarr), *minmax))
        #
        #     else:
        #         workdataarr = np.log10(np.abs(workdataarr))

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
                                  t[-1] == dims[-1] -1):
                    f.write('\n')

            # Always newlines at end
            f.write('\n\n')

    # If indicated, delete the source file
    if delsrc:
        os.remove(h5path)

def _validate_minmax(minmax, signed):
    """ [Docstring]

    """

    import sys

    if minmax[0] >= minmax[1]:
        print("Error: 'max' is not greater than 'min'")
        sys.exit(EXIT.CMDLINE)

    if not signed and minmax[0] < 0:
        print("Error: Negative 'min' in absolute thresholding mode")
        sys.exit(EXIT.CMDLINE)


def _validate_isofactor(isofactor, signed):
    """ [Docstring]

    """

    import argparse as ap
    import sys

    if isofactor[0] == 0.0:
        print("Error: 'isovalue' cannot be zero")
        sys.exit(EXIT.CMDLINE)

    if isofactor[1] <= 1.0:
        print("Error: 'factor' must be greater than one")
        sys.exit(EXIT.CMDLINE)

    if not signed and isofactor[0] < 0:
        print("Error: Negative 'isovalue' in absolute thresholding mode")
        sys.exit(EXIT.CMDLINE)


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


def main():

    import argparse as ap
    import numpy as np
    import os
    import sys

    # Retrieve the argument parser
    prs = _get_parser()

    # Parse known args, convert to dict, and leave unknown args in sys.argv
    ns, args_left = prs.parse_known_args()
    params = vars(ns)
    sys.argv = sys.argv[:1] + args_left

    # Retrieve path and file extension
    path = params[AP.PATH]
    ext = os.path.splitext(path)[1]

    # Check for existence
    if not os.path.isfile(path):
        print("File not found. Exiting...")
        sys.exit(EXIT.FILEREAD)

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
    def notNoneFalse(x):
        return x is not None and x is not False

    compargs = any(map(notNoneFalse, [comp, trunc, absolute,
                                      signed, nothresh,
                                      minmax, isofactor]))

    decompargs = any(map(notNoneFalse, [prec]))

    # Complain if nothresh specified but minmax or isofactor provided
    if nothresh and not (minmax is None and isofactor is None):
        print("Error: Thresholding parameter specified with --nothresh")
        sys.exit(EXIT.CMDLINE)

    # Complain if compression and decompression arguments mixed
    if compargs and decompargs:
        print("Error: Both compression and decompression options specified")
        sys.exit(EXIT.CMDLINE)

    # Convert and validate the thresholding inputs
    if minmax is not None:
        minmax = np.float_(minmax)
        _validate_minmax(minmax, signed)
    if isofactor is not None:
        isofactor = np.float_(isofactor)
        _validate_isofactor(isofactor, signed)

    # Complain if a thresholding mode is indicated but no
    # threshold values are provided
    if (absolute or signed) and (minmax is None and isofactor is None):
        print("Error: Thresholding mode specified but no values provided")
        sys.exit(EXIT.CMDLINE)

    # Check file extension as indication of execution mode
    if ext.lower() == '.h5cube':
        # Decompression mode
        if compargs:
            print("Error: compression arguments passed to "
                  "decompression operation")
            sys.exit(EXIT.CMDLINE)

        h5_to_cube(path, delsrc=delsrc, prec=prec)

    elif ext.lower() in ['.cube', '.cub']:
        # Compression mode
        if decompargs:
            print("Error: decompression arguments passed to "
                  "compression operation")
            sys.exit(EXIT.CMDLINE)

        if minmax is not None:
            # Min/max thresholding
            cube_to_h5(path, delsrc=delsrc, comp=comp, trunc=trunc,
                       thresh=True, signed=signed, minmax=minmax)
        elif isofactor is not None:
            # Isovalue thresholding
            cube_to_h5(path, delsrc=delsrc, comp=comp, trunc=trunc,
                       thresh=True, signed=signed, isofactor=isofactor)
        else:
            # No thresholding
            cube_to_h5(path, thresh=False, delsrc=delsrc, comp=comp,
                       trunc=trunc)

    else:
        print("File extension not recognized. Exiting...")
        sys.exit(EXIT.CMDLINE)


if __name__ == '__main__':
    main()

