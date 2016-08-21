import os
import sys

# Argparse constants
AP_PATH = 'path'
AP_DELETE = 'delete'
AP_COMPRESS = 'compress'
AP_TRUNC = 'truncate'

# h5py constants
H5_COMMENT1 = 'COMMENT1'
H5_COMMENT2 = 'COMMENT2'
H5_NATOMS = 'NATOMS'
H5_ORIGIN = 'ORIGIN'
H5_XAXIS = 'XAXIS'
H5_YAXIS = 'YAXIS'
H5_ZAXIS = 'ZAXIS'
H5_GEOM = 'GEOM'
H5_SIGNS = 'SIGNS'
H5_LOGDATA = 'LOGDATA'


def cube_to_h5(cubepath, delsrc, comp, trunc):

    import h5py as h5
    import itertools as itt
    import numpy as np
    import re

    with open(cubepath) as f:
        filedata = f.read()

    datalines = iter(filedata.splitlines())

    h5path = "{0}.h5".format(cubepath)
    if os.path.isfile(h5path):
        os.remove(h5path)

    hf = h5.File(h5path)

    # Comment lines
    hf.create_dataset(H5_COMMENT1, data=next(datalines))
    hf.create_dataset(H5_COMMENT2, data=next(datalines))

    # Number of atoms and origin
    elements = iter(next(datalines).split())
    natoms = abs(int(next(elements)))
    hf.create_dataset(H5_NATOMS, data=natoms)
    hf.create_dataset(H5_ORIGIN, data=np.array([float(next(elements))
                                             for i in range(3)]))

    # Dimensions and vectors
    dims = []
    for dsname in [H5_XAXIS, H5_YAXIS, H5_ZAXIS]:
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

    hf.create_dataset(H5_GEOM, data=geom)

    # Volumetric field data
    # Create one big iterator over a scientific notation regular
    #  expression for the remainder of the file

    # Regex pattern for lines of scientific notation
    p_scinot = re.compile("""
        -?                           # Optional leading negative sign
        \\d                          # Single leading digit
        \\.                          # Decimal point
        \\d+                         # Multiple digits
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

    # Loop over the respective dimensions
    for x in range(dims[0]):
        for y in range(dims[1]):
            for z in range(dims[2]):
                try:
                    val = float(next(dataiter).group(0))
                except StopIteration as e:
                    raise ValueError("Insufficient data in CUBE file") from e

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
    hf.create_dataset(H5_LOGDATA, data=logdataarr, compression="gzip",
                      compression_opts=comp, shuffle=True, scaleoffset=trunc)
    hf.create_dataset(H5_SIGNS, data=signsarr, compression="gzip",
                      compression_opts=comp, shuffle=True)

    # Close the h5 file
    hf.close()

    # If indicated, delete the source file
    if delsrc:
        os.remove(cubepath)


def h5_to_cube(h5path, delsrc):
    pass


def get_parser():

    import argparse as ap

    prs = ap.ArgumentParser(description="CUBE (de)compression via h5py",
                            epilog="When decompressing, all parameters but "
                                   "'{0}' and '{1}' are ignored."
                                   .format(AP_PATH, AP_DELETE))

    # Argument for the filename
    prs.add_argument(AP_PATH, action='store',
                     help="Path to file to be (de)compressed")

    # Argument to delete the source file; default is to keep
    prs.add_argument('-{0}'.format(AP_DELETE[0]), '--{0}'.format(AP_DELETE),
                     action='store_true',
                     help="Delete the source file after (de)compression")

    # gzip compression level
    prs.add_argument('-{0}'.format(AP_COMPRESS[0]),
                     '--{0}'.format(AP_COMPRESS),
                     action='store', default=9, type=int,
                     choices=list(range(10)),
                     help="gzip compression level (default 9)")

    # gzip truncation level
    prs.add_argument('-{0}'.format(AP_TRUNC[0]),
                     '--{0}'.format(AP_TRUNC),
                     action='store', default=5, type=int,
                     choices=list(range(1,10)),
                     help="gzip truncation width (default 5)")

    return prs


if __name__ == '__main__':

    prs = get_parser()

    # Parse known args, convert to dict, and leave unknown args in sys.argv
    ns, args_left = prs.parse_known_args()
    params = vars(ns)
    sys.argv = sys.argv[:1] + args_left

    # Retrieve path and file extension
    path = params[AP_PATH]
    ext = os.path.splitext(path)[1]

    # Retrieve other parameters
    delsrc = params[AP_DELETE]
    comp = params[AP_COMPRESS]
    trunc = params[AP_TRUNC]

    if ext == '.h5':
        h5_to_cube(path, delsrc)
    elif ext == '.cube':
        cube_to_h5(path, delsrc, comp, trunc)
    else:
        print("File extension not recognized. Exiting...")



