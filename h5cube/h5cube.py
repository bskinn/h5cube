# ------------------------------------------------------------------------------
# Name:        h5cube
# Purpose:     Script for h5py (de)compression of Gaussian CUBE files
#
# Author:      Brian Skinn
#                bskinn@alum.mit.edu
#
# Created:     20 Aug 2016
# Copyright:   (c) Brian Skinn 2016
# License:     The MIT License; see "license.txt" for full license terms
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
    SIGNS = 'SIGNS'
    LOGDATA = 'LOGDATA'

# Default values
class DEF(object):
    TRUNC = 5
    PREC = 5
    COMP = 9
    DEL = False
    THRESH = False


def exp_format(val, prec):
    """ [Docstring]

    """

    # Convert val using string formatting: Always a leading space;
    # positive values with another leading space; negatives with the negative
    # sign; one digit in front of the decimal, 'dec' digits after.
    # Capital 'E' for the exponent.
    out = " {{: #1.{0}E}}".format(prec).format(val)

    # Return the results
    return out


def cube_to_h5(cubepath, *, delsrc=DEF.DEL, comp=DEF.COMP, trunc=DEF.TRUNC,
               thresh=DEF.THRESH, signed=None, minmax=None, isofactor=None):
    """ [Docstring]

    """

    import h5py as h5
    import itertools as itt
    import numpy as np
    import os
    import re

    with open(cubepath) as f:
        filedata = f.read()

    datalines = iter(filedata.splitlines())

    h5path = os.path.splitext(cubepath)[0] + '.h5cube'
    if os.path.isfile(h5path):
        os.remove(h5path)

    hf = h5.File(h5path)

    # Comment lines
    hf.create_dataset(H5.COMMENT1, data=next(datalines))
    hf.create_dataset(H5.COMMENT2, data=next(datalines))

    # Number of atoms and origin
    elements = iter(next(datalines).split())
    natoms = abs(int(next(elements)))
    hf.create_dataset(H5.NATOMS, data=natoms)
    hf.create_dataset(H5.ORIGIN, data=np.array([float(next(elements))
                                             for i in range(3)]))

    # Dimensions and vectors
    dims = []
    for dsname in [H5.XAXIS, H5.YAXIS, H5.ZAXIS]:
        elements = iter(next(datalines).split())
        hf.create_dataset(dsname, data=np.array([float(next(elements))
                                                 for i in range(4)]))
        dims.append(int(hf[dsname].value[0]))

    # Geometry
    # Expect NATOMS lines with atom & geom data
    geom = np.zeros((natoms, 5))
    for i in range(natoms):
        elements = next(datalines).split()
        for j in range(5):
            geom[i, j] = elements[j]

    hf.create_dataset(H5.GEOM, data=geom)

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

    # Agglomerated iterator
    dataiter = itt.chain.from_iterable([p_scinot.finditer(l)
                                        for l in datalines])

    # Initialize the numpy objects
    logdataarr = np.zeros(dims)
    signsarr = np.zeros(dims)

    # Preassign the calculated minmax values if isofactored thresh
    # is enabled
    if thresh and isofactor is not None:
        # Populate minmax with the isovalue/factor based
        # threshold values
        minmax = np.zeros((2,))
        minmax[0] = isofactor[0] / isofactor[1]
        minmax[1] = isofactor[0] * isofactor[1]

    # Loop over the respective dimensions
    for x in range(dims[0]):
        for y in range(dims[1]):
            for z in range(dims[2]):
                try:
                    val = float(next(dataiter).group(0))
                except StopIteration as e:
                    raise ValueError("Insufficient data in CUBE file") from e

                # Threshold, if indicated
                if thresh:
                    if signed:
                        if val < minmax[0]:
                            val = minmax[0]
                        elif val > minmax[1]:
                            val = minmax[1]
                    else:
                        if np.abs(val) < minmax[0]:
                            val = np.sign(val) * minmax[0]
                        elif np.abs(val) > minmax[1]:
                            val = np.sign(val) * minmax[1]

                signsarr[x, y, z] = np.sign(val)
                logdataarr[x, y, z] = np.log10(np.abs(val))

    # Ensure exhausted
    try:
        next(dataiter)
    except StopIteration:
        pass
    else:
        raise ValueError("CUBE file dataset not exhausted")

    # Store the arrays, compressed
    hf.create_dataset(H5.LOGDATA, data=logdataarr, compression="gzip",
                      compression_opts=comp, shuffle=True, scaleoffset=trunc)
    hf.create_dataset(H5.SIGNS, data=signsarr, compression="gzip",
                      compression_opts=comp, shuffle=True)

    # Close the h5 file
    hf.close()

    # If indicated, delete the source file
    if delsrc:
        os.remove(cubepath)


def h5_to_cube(h5path, *, delsrc=DEF.DEL, prec=DEF.PREC):
    """ [Docstring]

    Less error/syntax checking here since presumably the data was
    parsed for validity when the .h5cube file was created.
    """

    import h5py as h5
    import os

    # Define the header block substitution strings
    hdr_3val = "{:5d}   {: 1.6f}   {: 1.6f}   {: 1.6f}"
    hdr_4val = "{:5d}   {: 1.6f}   {: 1.6f}   {: 1.6f}   {: 1.6f}"

    # Define the uncompressed filename
    cubepath = os.path.splitext(h5path)[0] + '.cube'

    # Open the source file
    hf = h5.File(h5path)

    # Delete any existing output file
    if os.path.isfile(cubepath):
        os.remove(cubepath)

    # Open the output file for writing as a context manager
    with open(cubepath, 'w') as f:
        # Write the two comment lines
        f.write(hf[H5.COMMENT1].value + '\n')
        f.write(hf[H5.COMMENT2].value + '\n')

        # Write the number-of-atoms and system origin line
        natoms = hf[H5.NATOMS].value
        f.write(hdr_3val.format(natoms, *(hf[H5.ORIGIN].value)) + '\n')

        # Write the three axes lines
        dims = []
        for dsname in [H5.XAXIS, H5.YAXIS, H5.ZAXIS]:
            ds = hf[dsname].value
            f.write(hdr_3val.format(int(ds[0]), *ds[1:]) + '\n')
            dims.append(int(ds[0]))

        # Write the geometry
        geom = hf[H5.GEOM].value
        for i in range(natoms):
            f.write(hdr_4val.format(int(geom[i,0]), *geom[i,1:]) + '\n')

        # Write the data blocks
        signs = hf[H5.SIGNS].value
        logvals = hf[H5.LOGDATA].value
        for x in range(dims[0]):
            for y in range(dims[1]):
                for z in range(dims[2]):
                    f.write(exp_format(signs[x, y, z] *
                                       10.**logvals[x, y, z], prec))
                    if z % 6 == 5:
                        f.write('\n')

                f.write('\n')

    # Close the h5 file
    hf.close()

    # If indicated, delete the source file
    if delsrc:
        os.remove(h5path)

def validate_minmax(minmax, signed):
    """ [Docstring]

    """

    import argparse as ap

    if minmax[0] >= minmax[1]:
        raise ap.ArgumentTypeError("'max' is not greater than 'min'")

    if not signed and minmax[0] < 0:
        raise ap.ArgumentTypeError("Negative 'min' in absolute "
                                   "thresholding mode")

def validate_isofactor(isofactor, signed):
    """ [Docstring]

    """

    import argparse as ap

    if isofactor[0] == 0.0:
        raise ap.ArgumentTypeError("'isovalue' cannot be zero")

    if isofactor[1] <= 1.0:
        raise ap.ArgumentTypeError("'factor' must be greater than one")

    if not signed and isofactor[0] < 0:
        raise ap.ArgumentTypeError("Negative 'isovalue' in absolute "
                                   "thresholding mode")
    

def get_parser():
    """ [Docstring]

    """

    import argparse as ap

    # Core parser
    prs = ap.ArgumentParser(description="Gaussian CUBE (de)compression "
                                        "via h5py")

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
                     help="path to .(h5)cube file to be (de)compressed")

    # Argument to delete the source file; default is to keep (core)
    prs.add_argument('-{0}'.format(AP.DELETE[0]), '--{0}'.format(AP.DELETE),
                     action='store_true',
                     help="delete the source file after (de)compression")

    # gzip compression level (compress)
    gp_comp.add_argument('-{0}'.format(AP.COMPRESS[0]),
                         '--{0}'.format(AP.COMPRESS),
                         action='store', default=DEF.COMP, type=int,
                         choices=list(range(10)),
                         metavar='#',
                         help="gzip compression level for volumetric "
                              "data (0-9, default {0})".format(DEF.COMP))

    # gzip truncation level (compress)
    gp_comp.add_argument('-{0}'.format(AP.TRUNC[0]),
                         '--{0}'.format(AP.TRUNC),
                         action='store', default=DEF.TRUNC, type=int,
                         choices=list(range(1,16)),
                         metavar='#',
                         help="gzip truncation width for volumetric "
                              "data (1-15, default {0})".format(DEF.TRUNC))

    # Absolute thresholding mode (compress -- threshold mode)
    meg_threshmode.add_argument('-{0}'.format(AP.ABSMODE[0]),
                                '--{0}'.format(AP.ABSMODE),
                                action='store_true',
                                help="absolute-value thresholding "
                                     "mode")

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
                                     "threshold specification")

    # Isovalue/factor threshold specification (compress -- threshold values)
    meg_threshvals.add_argument('-{0}'.format(AP.ISOFACTOR[0]),
                                '--{0}'.format(AP.ISOFACTOR),
                                action='store',
                                default=None,
                                nargs=2,
                                metavar='#',
                                help="Isovalue and multiplicative "
                                     "factor values for "
                                     "threshold specification")

    # Data block output precision (decompress)
    gp_decomp.add_argument('-{0}'.format(AP.PREC[0]),
                           '--{0}'.format(AP.PREC),
                           action='store', default=DEF.PREC, type=int,
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

    prs = get_parser()

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
        sys.exit(1)

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

    # Complain if nothresh specified but minmax or isofactor provided
    if nothresh and not (minmax is None and isofactor is None):
        raise ap.ArgumentTypeError("Invalid: Thresholding parameter specified "
                                   "with --nothresh")


    # Convert and validate the thresholding inputs
    if minmax is not None:
        minmax = np.float_(minmax)
        validate_minmax(minmax, signed)
    if isofactor is not None:
        isofactor = np.float_(isofactor)
        validate_isofactor(isofactor, signed)
    
    # Check file extension as indication of execution mode
    if ext == '.h5cube':
        # Decompression mode
        h5_to_cube(path, delsrc=delsrc, prec=prec)

    elif ext in ['.cube', '.cub']:
        # Compression mode
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
            cube_to_h5(path, delsrc=delsrc, comp=comp, trunc=trunc)

    else:
        print("File extension not recognized. Exiting...")
        sys.exit(1)


if __name__ == '__main__':
    main()

