#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'six',
    'pyzmq'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='zero_netcat',
    version='0.5.0',
    description="Netcat style utility using ZeroMQ sockets",
    long_description=readme + '\n\n' + history,
    author="Brett Warminski",
    author_email='bwarminski@gmail.com',
    url='https://github.com/bwarminski/zero_netcat',
    packages=[
        'zero_netcat',
    ],
    package_dir={'zero_netcat':
                 'zero_netcat'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='zero_netcat',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points = {
        'console_scripts' : [
            'zeronc = zero_netcat.zero_netcat:main'
        ]
    }
)
