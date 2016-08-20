import os
import sys

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


def cube_to_h5(cubepath):

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
    hf.create_dataset(COMMENT1, data=next(datalines))
    hf.create_dataset(COMMENT2, data=next(datalines))

    # Number of atoms and origin
    elements = iter(next(datalines).split())
    natoms = abs(int(next(elements)))
    hf.create_dataset(NATOMS, data=natoms)
    hf.create_dataset(ORIGIN, data=np.array([float(next(elements))
                                             for i in range(3)]))

    # Dimensions and vectors
    dims = []
    for dsname in [XAXIS, YAXIS, ZAXIS]:
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

    hf.create_dataset(GEOM, data=geom)

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
    dataiter = itt.chain(*(p_scinot.finditer(l) for l in datalines))

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
    hf.create_dataset(LOGDATA, data=logdataarr, compression="gzip",
                      compression_opts=9, shuffle=True, scaleoffset=5)
    hf.create_dataset(SIGNS, data=signsarr, compression="gzip",
                      compression_opts=9, shuffle=True)

    # Close the h5 file
    hf.close()


def h5_to_cube(path):
    pass


if __name__ == '__main__':

    path = sys.argv[1]
    ext = os.path.splitext(path)[1]

    if ext == '.h5':
        h5_to_cube(path)
    elif ext == '.cube':
        cube_to_h5(path)

