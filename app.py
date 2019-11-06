# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import TypeVar, List, Dict, Union, Type
import ssl
from yaml import safe_load
from flask import Flask, render_template

_VSlide = Dict[str, Union[str, List[Dict[str, str]]]]
_HSlide = Dict[str, Union[str, List[Dict[str, str]], List[_VSlide]]]
_Data = Dict[str, Union[str, bool, List[_HSlide]]]
T = TypeVar('T')

app = Flask(__name__)


def load_yaml() -> _Data:
    with open("reveal.yml", 'r', encoding='utf-8') as f:
        return safe_load(f)


def check_type(t: Type[T], value: Union[str, bool, list, dict]) -> T:
    if not isinstance(value, t):
        raise TypeError(f"expect type: {t}, get: {type(value)}")
    return value


def slide_block(slide: _VSlide):
    """Ensure slide attributes."""
    slide['title'] = check_type(str, slide.get('title', ""))
    slide['doc'] = check_type(str, slide.get('doc', ""))
    slide['math'] = check_type(str, slide.get('math', ""))
    slide['img'] = check_type(list, slide.get('img', []))
    for img in slide['img']:  # type: Dict[str, str]
        img['src'] = check_type(str, img.get('src', ""))
        img['width'] = check_type(str, img.get('width', ""))
        img['height'] = check_type(str, img.get('height', ""))


@app.route('/')
def presentation() -> str:
    config = load_yaml()
    nav: List[_HSlide] = check_type(list, config.get('nav', []))
    for n in nav:
        slide_block(n)
        n['sub'] = check_type(list, n.get('sub', []))
        for sn in n['sub']:  # type: _VSlide
            slide_block(sn)
    return render_template(
        "presentation.html",
        title=check_type(str, config.get('title', "Untitled")),
        icon=check_type(str, config.get('icon', "img/icon.png")),
        history=str(check_type(bool, config.get('history', True))).lower(),
        transition=check_type(str, config.get('transition', 'linear')),
        nav=nav,
    )


def main() -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('localhost.crt', 'localhost.key')
    app.run(host='127.0.0.1', port=9443, debug=True, ssl_context=context)


if __name__ == "__main__":
    main()
