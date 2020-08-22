# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from sys import stdout
from os.path import abspath, dirname, isfile, join
from flask import Flask, render_template, request, jsonify, Response
from yaml import safe_load
from jsonschema import validate
from reveal_yaml.app import PROJECT, Config, render_slides

ROOT = abspath(dirname(__file__))
START = "<h1>Press the compile button to render the slides!</h1>"
PREVIEW = {}
ERROR = {}

app = Flask(__name__)
path = abspath(join(ROOT, 'schema.yaml'))
if not isfile(path):
    raise ValueError("load schema failed!")
with open(path, 'r') as f:
    SCHEMA = safe_load(f)
if not PROJECT:
    PROJECT = join(ROOT, 'blank.yaml')
with open(PROJECT, 'r', encoding='utf-8') as f:
    SAVED = f.read()
del path, f


@app.route('/_handler')
def _handler() -> Response:
    res_id = request.args.get('id')
    try:
        # Validate
        config = safe_load(request.args.get('config'))
        validate(config, SCHEMA)
    except Exception as e:
        from traceback import format_exc
        stdout.write(format_exc())
        ERROR[res_id] = f"<pre>{format_exc()}\n{e}</pre>"
        if len(ERROR) > 50:
            ERROR.pop(min(ERROR))
        return jsonify(validated=False)
    # Preview
    PREVIEW[res_id] = render_slides(
        Config(**{k.replace('-', '_'): v for k, v in config.items()}))
    if len(PREVIEW) > 50:
        PREVIEW.pop(min(PREVIEW))
    return jsonify(validated=True)


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def server_error(e: Exception) -> str:
    """Handle server error."""
    from traceback import format_exc
    stdout.write(format_exc())
    return f"<pre>{format_exc()}\n{e}</pre>"


@app.route('/preview')
def preview() -> str:
    """Render preview."""
    res_id = request.args.get('id')
    if res_id == 0:
        return START
    return PREVIEW.get(res_id, START)


@app.route('/error')
def error() -> str:
    """Render error."""
    return ERROR.get(request.args.get('id'), START)


@app.route('/')
def index() -> str:
    """The editor."""
    return render_template("editor.html", saved=SAVED)
