from setuptools import setup, find_packages

setup(
    name          = 'svj_genprod',
    version       = '0.1',
    license       = 'BSD 3-Clause License',
    description   = 'Package for MC generation of semi-visible jet events',
    url           = 'https://github.com/tklijnsma/svjgenprod.git',
    download_url  = 'https://github.com/tklijnsma/svjgenprod/archive/v0_1.tar.gz',
    author        = 'Thomas Klijnsma',
    author_email  = 'tklijnsm@gmail.com',
    packages      = find_packages(),
    zip_safe      = False,
    scripts       = [
        'svj/bin/svj-genprod-batch',
        ],
    )
