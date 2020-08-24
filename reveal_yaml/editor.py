# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Dict, Union, Optional
from os.path import basename, join
from distutils.dir_util import copy_tree, mkpath
from shutil import make_archive, rmtree
from io import BytesIO
from time import time_ns
from tempfile import TemporaryDirectory
from flask import Flask, Response, render_template, request, jsonify, send_file
from yaml import safe_load
from jsonschema import validate
from reveal_yaml import __version__
from .slides import ROOT, Config, render_slides
from .utility import load_file, valid_config

_HELP = ""
_SAVED = load_file(join(ROOT, 'blank.yaml'))
_SCHEMA: Optional[Dict[str, dict]] = None
_CONFIG: Dict[int, dict] = {}

app = Flask(__name__)


def load_schema_doc() -> None:
    global _SCHEMA, _HELP
    if _HELP and _SCHEMA is not None:
        return
    _SCHEMA = safe_load(load_file(join(ROOT, 'schema.yaml')))
    config = safe_load(load_file(join(ROOT, 'reveal.yaml')))
    _HELP = render_slides(Config(**valid_config(config)))


def set_saved(path: str) -> None:
    """Set saved project."""
    if not path:
        return
    global _SAVED
    _SAVED = load_file(path)


@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def server_error(e: Exception) -> str:
    """Handle server error, especially for the previewer."""
    from traceback import format_exc
    return f"<pre>{format_exc()}\n{e}</pre>"


@app.route('/preview/<int:res_id>', methods=['GET', 'POST'])
def preview(res_id: int) -> Union[str, Response]:
    """Render preview."""
    if request.method == 'POST':
        # Re-generate ID by time
        res_id = time_ns()
        _CONFIG[res_id] = request.get_json()
        if len(_CONFIG) > 200:
            _CONFIG.pop(min(_CONFIG))
        # Important: INT will loss value!
        return jsonify(id=str(res_id))
    load_schema_doc()
    if res_id == 0:
        return _HELP
    config = _CONFIG[res_id]
    try:
        validate(config, _SCHEMA)
    except Exception as e:
        from traceback import format_exc
        return f"<pre>{format_exc()}\n{e}</pre>"
    return render_slides(Config(**valid_config(config)))


@app.route('/pack/<int:res_id>')
def pack(res_id: int) -> Response:
    """Build and provide zip file for user download."""
    if res_id not in _CONFIG:
        return send_file(BytesIO(), attachment_filename='empty.txt',
                         as_attachment=True)
    with TemporaryDirectory(suffix=f"{res_id}") as path:
        build_path = join(path, "reveal")
        mkpath(build_path)
        config = Config(**_CONFIG[res_id])
        with open(join(build_path, "index.html"), 'w+', encoding='utf-8') as f:
            f.write(render_slides(config, rel_url=True))
        copy_tree(join(ROOT, 'static'), join(build_path, 'static'))
        rmtree(join(build_path, 'static', 'ace'))
        for name, enabled in config.plugin.as_dict():
            if not enabled:
                rmtree(join(build_path, 'static', 'plugin', name))
        archive = make_archive(build_path, 'zip', build_path)
        with open(archive, 'rb') as f:
            mem = BytesIO(f.read())
    archive = basename(archive)
    return send_file(mem, as_attachment=True, attachment_filename=archive)


@app.route('/')
def index() -> str:
    """The editor."""
    return render_template("editor.html", saved=_SAVED, version=__version__,
                           author=__author__, license=__license__,
                           copyright=__copyright__, email=__email__)
