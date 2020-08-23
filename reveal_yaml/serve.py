# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from flask import Flask
from werkzeug.exceptions import HTTPException
from .slides import render_slides, load_yaml, Config, HSlide

app = Flask(__name__)


@app.route('/')
def index() -> str:
    """Generate the presentation."""
    return render_slides(Config(**load_yaml()))


@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def server_error(e: HTTPException) -> str:
    """Error pages."""
    from traceback import format_exc
    title = f"{e.code} {e.name}"
    return render_slides(
        Config(title=title, theme='night', nav=[HSlide(
            title=title,
            doc=f"```sh\n{format_exc()}\n{e.description}\n```"
        )]))
