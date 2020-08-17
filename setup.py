# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Iterator
from re import MULTILINE, search
from os import walk
from os.path import join
from setuptools import setup, find_packages


def read(path: str):
    with open(path, 'r') as f:
        return f.read()


def find_version(path: str):
    m = search(r"^__version__ = ['\"]([^'\"]*)['\"]", read(path), MULTILINE)
    if m:
        return m.group(1)
    raise RuntimeError("Unable to find version string.")


def package_files(path: str) -> Iterator[str]:
    for root, _, filenames in walk(path):
        for filename in filenames:
            yield join('..', root, filename)


extra_files = list(package_files(join('reveal_yaml', '.github')))
extra_files.extend(package_files(join('reveal_yaml', 'static')))
extra_files.extend(package_files(join('reveal_yaml', 'templates')))

setup(
    name='reveal_yaml',
    version=find_version(join('reveal_yaml', '__init__.py')),
    author=__author__,
    author_email=__email__,
    license=__license__,
    description="A YAML, Markdown, reveal.js based Flask application. "
                "Supports gh-pages deployment actions.",
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    url="https://kmolyuan.github.io/reveal-yaml",
    packages=find_packages(),
    package_data={'reveal_yaml': ['py.typed', 'blank.yaml', 'schema.*'],
                  '': extra_files},
    entry_points={'console_scripts': ['rym=reveal_yaml.__main__:main']},
    zip_safe=False,
    python_requires=">=3.7",
    options={'bdist_wheel': {'python_tag': 'cp37.cp38'}},
    install_requires=read('requirements.txt').splitlines(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ]
)
