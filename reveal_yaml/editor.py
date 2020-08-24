# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Dict
from os.path import abspath, basename, isfile, join
from distutils.dir_util import copy_tree, mkpath
from shutil import make_archive, rmtree
from io import BytesIO
from tempfile import TemporaryDirectory
from flask import Flask, Response, render_template, request, jsonify, send_file
from yaml import safe_load
from jsonschema import validate
from reveal_yaml.slides import ROOT, Config, render_slides

START = "<h1>Press the compile button to render the slides!</h1>"
PREVIEW: Dict[int, dict] = {}

app = Flask(__name__)
_path = abspath(join(ROOT, 'schema.yaml'))
if not isfile(_path):
    raise ValueError("load schema failed!")
with open(_path, 'r') as _f:
    SCHEMA = safe_load(_f)
del _path
SAVED = ""


def set_saved(path: str) -> None:
    """Set saved project."""
    if not path:
        path = join(ROOT, 'blank.yaml')
    global SAVED
    with open(path, 'r', encoding='utf-8') as f:
        SAVED = f.read()


@app.route('/_handler/<int:res_id>', methods=['GET', 'POST'])
def _handler(res_id: int) -> Response:
    PREVIEW[res_id] = {k.replace('-', '_'): v
                       for k, v in request.get_json().items()}
    if len(PREVIEW) > 200:
        PREVIEW.pop(min(PREVIEW))
    return jsonify(validated=True)


@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def server_error(e: Exception) -> str:
    """Handle server error, especially for the previewer."""
    from traceback import format_exc
    return f"<pre>{format_exc()}\n{e}</pre>"


@app.route('/preview/<int:res_id>')
def preview(res_id: int) -> str:
    """Render preview."""
    if res_id == 0 or res_id not in PREVIEW:
        return START
    config = PREVIEW[res_id]
    try:
        validate(config, SCHEMA)
    except Exception as e:
        from traceback import format_exc
        return f"<pre>{format_exc()}\n{e}</pre>"
    return render_slides(Config(**config))


@app.route('/pack/<int:res_id>')
def pack(res_id: int) -> Response:
    """Build and provide zip file for user download."""
    if res_id not in PREVIEW:
        return send_file(BytesIO(), attachment_filename='empty.txt',
                         as_attachment=True)
    with TemporaryDirectory(suffix=f"{res_id}") as path:
        build_path = join(path, "reveal")
        mkpath(build_path)
        config = Config(**PREVIEW[res_id])
        with open(join(build_path, "index.html"), 'w+', encoding='utf-8') as f:
            f.write(render_slides(config, rel_url=True))
        copy_tree(join(ROOT, 'static'), join(build_path, 'static'))
        rmtree(join(build_path, 'static', 'ace'))
        archive = make_archive(build_path, 'zip', build_path)
        with open(archive, 'rb') as f:
            mem = BytesIO(f.read())
    archive = basename(archive)
    return send_file(mem, as_attachment=True, attachment_filename=archive)


@app.route('/')
def index() -> str:
    """The editor."""
    return render_template("editor.html", saved=SAVED)
