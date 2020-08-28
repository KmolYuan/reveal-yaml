# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Dict, Any
from os import remove, getcwd
from os.path import isfile, join, abspath, dirname
from urllib.parse import urlparse
from requests import get
from flask import Flask

ROOT = abspath(dirname(__file__))
PWD = abspath(getcwd())


def is_url(path: str) -> bool:
    """Return true if the path is url."""
    u = urlparse(path)
    return all((u.scheme, u.netloc, u.path))


def serve(pwd: str, app: Flask, ip: str, port: int = 0) -> None:
    """Serve the app."""
    key = (join(pwd, 'localhost.crt'), join(pwd, 'localhost.key'))
    if isfile(key[0]) and isfile(key[1]):
        from ssl import SSLContext, PROTOCOL_TLSv1_2
        context = SSLContext(PROTOCOL_TLSv1_2)
        context.load_cert_chain(key[0], key[1])
        app.run(ip, port, ssl_context=context)
    else:
        app.run(ip, port)


def valid_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Replace minus sign with an underscore."""
    for key in tuple(data):
        data[key.replace('-', '_')] = data.pop(key)
    return data


def load_file(path: str) -> str:
    """Load file from the path."""
    if is_url(path):
        return get(path).text
    if not path or not isfile(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def dl(url: str, dist: str) -> None:
    """Download file if not exist."""
    if isfile(dist):
        return
    with open(dist, 'wb') as f:
        f.write(get(url).content)


def rm(path: str) -> None:
    """Remove file if exist."""
    if isfile(path):
        remove(path)
