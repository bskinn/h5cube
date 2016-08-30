from setuptools import setup

setup(
    name='h5cube',
    version='0.1.post2',
    provides=['h5cube'],
    requires=['h5py (>=2.4)', 'numpy (>=1.6.1)'],
    packages=['h5cube', 'h5cube.test'],
    url='https://www.github.com/bskinn/h5cube',
    license='MIT License',
    author='Brian Skinn',
    author_email='bskinn@alum.mit.edu',
    description='Gaussian CUBE File Compression Utility',
    classifiers=['License :: OSI Approved :: MIT License',
                 'Natural Language :: English',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Topic :: Scientific/Engineering',
                 'Topic :: System :: Archiving :: Compression',
                 'Topic :: Utilities',
                 'Development Status :: 4 - Beta'],
    entry_points={
        'console_scripts': [
            'h5cube = h5cube.h5cube:main'
                           ]
                  }
)
