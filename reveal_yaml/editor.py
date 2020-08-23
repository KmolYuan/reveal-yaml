# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Dict
from os.path import abspath, dirname, isfile, join
from flask import Flask, render_template, request, jsonify, Response
from yaml import safe_load
from jsonschema import validate
from reveal_yaml.slides import PROJECT, Config, render_slides

ROOT = abspath(dirname(__file__))
START = "<h1>Press the compile button to render the slides!</h1>"
PREVIEW: Dict[int, dict] = {}

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


def get_id() -> int:
    """Get the current id from path argument."""
    res_id = request.args.get('id')
    if res_id is None:
        raise ValueError("invalid id")
    return int(res_id)


@app.route('/_handler', methods=['GET', 'POST'])
def _handler() -> Response:
    res_id = get_id()
    PREVIEW[res_id] = request.get_json()
    if len(PREVIEW) > 50:
        PREVIEW.pop(min(PREVIEW))
    return jsonify(validated=True)


@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def server_error(e: Exception) -> str:
    """Handle server error, especially for the previewer."""
    from traceback import format_exc
    return f"<pre>{format_exc()}\n{e}</pre>"


@app.route('/preview')
def preview() -> str:
    """Render preview."""
    res_id = get_id()
    if res_id == 0:
        return START
    config = PREVIEW[res_id]
    try:
        validate(config, SCHEMA)
    except Exception as e:
        from traceback import format_exc
        return f"<pre>{format_exc()}\n{e}</pre>"
    return render_slides(
        Config(**{k.replace('-', '_'): v for k, v in config.items()}))


@app.route('/')
def index() -> str:
    """The editor."""
    return render_template("editor.html", saved=SAVED)
