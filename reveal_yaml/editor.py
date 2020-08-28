# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import Union
from os.path import basename, join
from shutil import make_archive
from io import BytesIO
from tempfile import TemporaryDirectory
from time import time_ns
from json import loads
from yaml import safe_load
from jsonschema import validate
from flask import Flask, Response, render_template, request, jsonify, send_file
from dataset import connect, Table
from reveal_yaml import __version__
from .slides import ROOT, Config, render_slides, copy_project
from .utility import load_file, valid_config

app = Flask(__name__)
db = connect('sqlite:///' + join(ROOT, 'swap.db'))
if set(db.tables) != {'doc', 'schema', 'swap'}:
    tb1: Table = db.create_table('doc')
    tb1.create_column('doc', db.types.text)
    tb2: Table = db.create_table('schema')
    tb2.create_column('json', db.types.json)
    tb3: Table = db.create_table('swap')
    tb3.create_column('json', db.types.json)
else:
    tb1 = db['doc']
    tb2 = db['schema']
    tb3 = db['swap']


def load_schema_doc() -> None:
    if tb1.find_one(id=0) is not None:
        return
    config = safe_load(load_file(join(ROOT, 'reveal.yaml')))
    tb1.insert({'id': 0, 'doc': render_slides(Config(**valid_config(config)))})
    tb1.insert({'id': 1, 'doc': load_file(join(ROOT, 'blank.yaml'))})
    tb2.insert({'id': 0, 'json': loads(load_file(join(ROOT, 'schema.json')))})


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
        tb3.insert({'id': res_id, 'json': request.get_json()})
        if len(tb3) > 300:
            tb3.delete(id=tb3.find_one(order_by=['id'])['id'])
        # Use integers will loss the value!
        return jsonify(id=str(res_id))
    load_schema_doc()
    if res_id == 0:
        return tb1.find_one(id=0)['doc']
    config = tb3.find_one(id=res_id)['json']
    try:
        validate(config, tb2.find_one(id=0)['json'])
    except Exception as e:
        from traceback import format_exc
        return f"<pre>{format_exc()}\n{e}</pre>"
    return render_slides(Config(**valid_config(config)))


@app.route('/pack/<int:res_id>')
def pack(res_id: int) -> Response:
    """Build and provide zip file for user download."""
    row = tb3.find_one(id=res_id)
    if row is None:
        return send_file(BytesIO(), attachment_filename='empty.txt',
                         as_attachment=True)
    with TemporaryDirectory(suffix=f"{res_id}") as path:
        config = Config(**row['json'])
        build_path = join(path, "reveal")
        copy_project(config, ROOT, build_path)
        archive = make_archive(build_path, 'zip', build_path)
        with open(archive, 'rb') as f:
            mem = BytesIO(f.read())
    archive = basename(archive)
    return send_file(mem, as_attachment=True, attachment_filename=archive)


@app.route('/')
def index() -> str:
    """The editor."""
    saved = tb1.find_one(id=1)
    return render_template("editor.html", version=__version__,
                           author=__author__, license=__license__,
                           copyright=__copyright__, email=__email__,
                           saved="" if saved is None else saved['doc'])
