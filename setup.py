# -*- coding: utf-8 -*-

from typing import Iterator
from os import walk
from os.path import join
from setuptools import setup


def package_files(path: str) -> Iterator[str]:
    for root, _, filenames in walk(path):
        for filename in filenames:
            if not filename.endswith('.py'):
                yield join('..', root, filename)


extra_files = list(package_files(join('reveal_yaml', '.github')))
extra_files.extend(package_files(join('reveal_yaml', 'static')))
extra_files.extend(package_files(join('reveal_yaml', 'templates')))

setup(package_data={'reveal_yaml': ['py.typed', '*.yaml', 'schema.*'],
                    '': extra_files})
