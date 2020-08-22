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
PREVIEW = {'o': "<h1>Press the compile button to render the slides!</h1>"}

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
    try:
        # Validate
        config = safe_load(request.args.get('config'))
        validate(config, SCHEMA)
    except Exception as e:
        from traceback import format_exc
        stdout.write(format_exc())
        return jsonify(validated=False, msg=f"<p>{e}</p>")
    # Preview
    PREVIEW[request.args.get('id')] = render_slides(
        Config(**{k.replace('-', '_'): v for k, v in config.items()}))
    if len(PREVIEW) > 10:
        PREVIEW.pop(min(PREVIEW))
    return jsonify(validated=True)


@app.route('/preview')
def preview() -> str:
    """Render preview."""
    return PREVIEW[request.args.get('id', 'o')]


@app.route('/')
def index() -> str:
    """The editor."""
    return render_template("editor.html", saved=SAVED)
