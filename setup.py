#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pip install twine
setup.py sdist bdist_wheel
# TEST PYPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
"""
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from django_celery_async_view/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("django_celery_async_view", "__init__.py")


if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django_celery_async_view',
    version=version,
    description='Asynchronously load view or download file in django.',
    long_description=readme + '\n\n' + history,
    author='Eero Paukkonen',
    author_email='eero.paukkonen@gmail.com',
    url='https://github.com/EeroPaukkonen/django_celery_async_view',
    packages=[
        'django_celery_async_view',
    ],
    include_package_data=True,
    install_requires=[
        'django-db-file-storage==0.4.3'
    ],
    license="MIT",
    zip_safe=False,
    keywords=['django_celery_async_view', 'django', 'celery'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
