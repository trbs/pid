import os
import re
import codecs
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))


# Read the version number from a source file.
# Why read it, and not import?
# see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Get the long description from the relevant file
with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pid",
    version=find_version('pid/__init__.py'),
    description="Pidfile featuring stale detection and file-locking, can also be used as context-manager or decorator",
    long_description=long_description,
    url='https://github.com/trbs/pid/',
    author='Trbs',
    author_email='trbs@trbs.net',
    license='ASL',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='pid pidfile context manager decorator',
    packages=["pid"],
    install_requires=[
        'psutil>=5.4.8 ; sys_platform == "win32"',
    ],
    test_suite='nose.collector',
    tests_require=['nose>=1.0'],
)
