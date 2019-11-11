# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import overload, TypeVar, Tuple, List, Dict, Union, Type
from urllib.parse import urlparse
from yaml import safe_load
from flask import Flask, render_template, url_for
from flask_frozen import relative_url_for

_VSlide = Dict[str, Union[str, List[Dict[str, str]]]]
_HSlide = Dict[str, Union[str, List[Dict[str, str]], List[_VSlide]]]
_Data = Dict[str, Union[str, bool, List[_HSlide]]]
_YamlValue = Union[int, float, str, bool, list, dict]
T = TypeVar('T', bound=_YamlValue)
U = TypeVar('U', bound=_YamlValue)

app = Flask(__name__)


def load_yaml() -> _Data:
    """Load "reveal.yml" project."""
    with open("reveal.yml", 'r', encoding='utf-8') as f:
        return safe_load(f)


@overload
def cast(t: Type[T], value: _YamlValue) -> T: ...


@overload
def cast(t: Tuple[Type[T], Type[U]], value: _YamlValue) -> Union[T, U]: ...


def cast(t, value):
    """Check the type of value."""
    if not isinstance(value, t):
        raise TypeError(f"expect type: {t}, get: {type(value)}")
    return value


def uri(path: str) -> str:
    """Handle relative path and URIs."""
    if not path:
        return ""
    u = urlparse(path)
    if all([u.scheme, u.netloc, u.path]):
        return path
    if app.config.get('FREEZER_RELATIVE_URLS', False):
        return relative_url_for('static', filename=path)
    else:
        return url_for('static', filename=path)


def slide_block(slide: _VSlide):
    """Ensure slide attributes."""
    slide['title'] = cast(str, slide.get('title', ""))
    slide['doc'] = cast(str, slide.get('doc', ""))
    slide['math'] = cast(str, slide.get('math', ""))
    slide['embed'] = uri(cast(str, slide.get('embed', "")))
    slide['img'] = cast(list, slide.get('img', []))
    for img in slide['img']:  # type: Dict[str, str]
        img['src'] = uri(cast(str, img.get('src', "")))
        img['width'] = cast(str, img.get('width', ""))
        img['height'] = cast(str, img.get('height', ""))


@app.route('/')
def presentation() -> str:
    """Generate the presentation."""
    config = load_yaml()
    nav: List[_HSlide] = cast(list, config.get('nav', []))
    for n in nav:
        slide_block(n)
        n['sub'] = cast(list, n.get('sub', []))
        for sn in n['sub']:  # type: _VSlide
            slide_block(sn)
    return render_template(
        "presentation.html",
        title=cast(str, config.get('title', "Untitled")),
        description=cast(str, config.get('description', "")),
        author=cast(str, config.get('author', "")),
        theme=cast(str, config.get('theme', 'serif')),
        icon=uri(cast(str, config.get('icon', "img/icon.png"))),
        default_style=cast(bool, config.get('default-style', True)),
        extra_style=cast(str, config.get('extra-style', "")),
        watermark=uri(cast(str, config.get('watermark', ""))),
        watermark_size=cast(str, config.get('watermark-size', "")),
        history=str(cast(bool, config.get('history', True))).lower(),
        transition=cast(str, config.get('transition', 'linear')),
        slide_num=cast((str, bool), config.get('slide-num', 'c/t')),
        nav=nav
    )


def main() -> None:
    """Main function startup with SSH."""
    from ssl import SSLContext, PROTOCOL_TLSv1_2
    context = SSLContext(PROTOCOL_TLSv1_2)
    context.load_cert_chain('localhost.crt', 'localhost.key')
    app.run(host='127.0.0.1', port=9443, debug=True, ssl_context=context)


if __name__ == "__main__":
    main()
