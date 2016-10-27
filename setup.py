from setuptools import setup, find_packages

setup(
    name='plankton',
    version='1.0',
    description='A platform for development of stateful hardware device simulations.',
    url='https://github.com/DMSC-Instrument-Data/plankton',
    author='Michael Hart, Michael Wedel',
    author_email='Michael Hart <Michael.Hart@stfc.ac.uk>, Michael Wedel <Michael.Wedel@esss.se>',
    license='GPL v3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console'
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='hardware simulation controls',
    packages=find_packages(exclude=['docs', 'test']),

    install_requires=['six', 'pyzmq', 'json-rpc'],

    extras_require={
        'EPICS': ['pcaspy'],
        'dev': ['flake8', 'mock>=1.0.1'],
    },

    entry_points={
        'console_scripts': [
            'plankton=plankton.scripts.run:run_simulation',
            'plankton-control=plankton.scripts.control:control_simulation'
        ],
    },
)
