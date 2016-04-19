#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directory, *args)


def get_version():
    """Get the version of `package` (by extracting it from the source code)."""
    module_path = get_absolute_path('flas', '__init__.py')
    with open(module_path) as handle:
        for line in handle:
            match = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']$', line)
            if match:
                return match.group(1)
    raise Exception("Failed to extract version from %s!" % module_path)


requirements = [
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='flask-sqa-restless',
    version=get_version(),
    description="Flask REST API Framework for SQLAlchemy",
    long_description=readme,
    author="Ritesh Kadmawala",
    author_email='ritesh@loanzen.in',
    url='https://github.com/loanzen/flask_sqa_restless',
    packages=[
        'flask_sqa_restless',
    ],
    package_dir={'flask_sqa_restless':
                 'flask_sqa_restless'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='flask-sqa-restless, REST Framework',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Flask',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development:: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',

    ],
    test_suite='tests',
    tests_require=test_requirements
)