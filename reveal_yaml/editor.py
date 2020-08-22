# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from sys import stdout
from os.path import abspath, dirname, isfile, join
from flask import Flask, render_template, request, jsonify
from yaml import safe_load
from jsonschema import validate
from reveal_yaml.app import PROJECT, Config, render_slides

ROOT = abspath(dirname(__file__))
PREVIEW = ""
app = Flask(__name__)
path = abspath(join(ROOT, 'schema.yaml'))
if not isfile(path):
    raise ValueError("load schema failed!")
with open(path, 'r') as f:
    SCHEMA = safe_load(f)
del path


@app.route('/_handler')
def _handler():
    try:
        # Validate
        config = safe_load(request.args.get('config'))
        validate(config, SCHEMA)
    except Exception as e:
        from traceback import format_exc
        stdout.write(format_exc())
        return jsonify(validated=False, msg=f"<p>{e}</p>")
    # Preview
    global PREVIEW
    PREVIEW = render_slides(Config(**{k.replace('-', '_'): v
                                      for k, v in config.items()}))
    return jsonify(validated=True)


@app.route('/_preview')
def _preview() -> str:
    """Render preview."""
    return PREVIEW


@app.route('/')
def index() -> str:
    """The editor page."""
    return render_template("editor.html")
