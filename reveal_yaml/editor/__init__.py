# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from os.path import abspath, dirname
from flask import Flask, request

root = abspath(dirname(__file__))
editor_app = Flask(__name__)


@editor_app.route('/')
def index() -> str:
    return "Editor: Hello world!"


@editor_app.route('/exit', methods=['POST'])
def shutdown():
    """Manually close the server."""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError("wrong server")
    func()
    return "Server shutting down..."
