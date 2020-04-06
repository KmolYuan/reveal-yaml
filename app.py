# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import overload, TypeVar, Tuple, List, Dict, Union, Type
from sys import argv
from werkzeug.exceptions import HTTPException
from urllib.parse import urlparse
from yaml import safe_load
from yaml.parser import ParserError
from flask import Flask, render_template, url_for, abort
from flask_frozen import Freezer, relative_url_for

_Opt = Dict[str, str]
_VSlide = Dict[str, Union[str, Union[List[_Opt], _Opt]]]
_HSlide = Dict[str, Union[str, List[_Opt], List[_VSlide]]]
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
    """Check value type."""
    if value is None:
        # Create an empty instance
        return t()
    elif not isinstance(value, t):
        abort(500, f"expect type: {t}, get: {type(value)}")
        return value
    else:
        return value


def uri(path: str) -> str:
    """Handle the relative path and URIs."""
    if not path:
        return ""
    u = urlparse(path)
    if all((u.scheme, u.netloc, u.path)):
        return path
    if app.config.get('FREEZER_RELATIVE_URLS', False):
        return relative_url_for('static', filename=path)
    else:
        return url_for('static', filename=path)


def pixel(value: Union[int, str]) -> str:
    """Support pure number input of the size."""
    if isinstance(value, str):
        return value
    return f"{value}pt"


def sized_block(block: _Opt, w: str = "", h: str = ""):
    """Ensure the attributes of sized resource."""
    block['src'] = uri(cast(str, block.get('src', "")))
    block['width'] = pixel(cast((int, str), block.get('width', w)))
    block['height'] = pixel(cast((int, str), block.get('height', h)))


def slide_block(slide: _VSlide):
    """Ensure the attributes of slide."""
    slide['id'] = cast(str, slide.get('id', ""))
    slide['title'] = cast(str, slide.get('title', ""))
    slide['doc'] = cast(str, slide.get('doc', ""))
    slide['math'] = cast(str, slide.get('math', ""))
    # Youtube link
    slide['youtube'] = cast(dict, slide.get('youtube', {}))
    sized_block(slide['youtube'])
    # Embeded resource
    slide['embed'] = cast(dict, slide.get('embed', {}))
    sized_block(slide['embed'], '1000px', '450px')
    # Images
    imgs: Union[List[_Opt], _Opt] = cast((list, dict), slide.get('img', []))
    if isinstance(imgs, dict):
        imgs: List[_Opt] = [imgs]
    slide['img'] = imgs
    for img in imgs:
        img['label'] = cast(str, img.get('label', ""))
        sized_block(img)
    # Fragment
    fragment: _Opt = cast(dict, slide.get('fragment', {}))
    slide['fragment'] = fragment
    for name, value in fragment.items():
        fragment[name] = "" if value is None else " " + value


def _outline(nav: List[_HSlide], nest: bool) -> str:
    """Generate markdown outline."""
    doc = []
    for n in nav[1:]:
        title = n.get('title', "")
        if title:
            doc.append(f"+ {title}")
        if not nest:
            continue
        n['sub'] = cast(list, n.get('sub', []))
        sub: List[_VSlide] = n['sub']
        for sn in sub:
            title = sn.get('title', "")
            if title:
                doc.append("  " + f"+ {title}")
    return '\n'.join(doc)


@app.route('/')
def presentation() -> str:
    """Generate the presentation."""
    try:
        config = load_yaml()
    except ParserError as e:
        abort(500, e)
        return ""
    outline = cast(int, config.get('outline', 0))
    nav: List[_HSlide] = cast(list, config.get('nav', []))
    for i in range(len(nav)):
        n = nav[i]
        slide_block(n)
        n['sub'] = cast(list, n.get('sub', []))
        sub: List[_VSlide] = n['sub']
        if nav[1:] and i == 0 and outline > 0:
            sub.append({'title': "Outline", 'doc': _outline(nav, outline >= 2)})
        for sn in sub:
            slide_block(sn)
    footer = cast(dict, config.get('footer', {}))
    footer['label'] = cast(str, footer.get('label', ""))
    footer['link'] = uri(cast(str, footer.get('link', "")))
    sized_block(footer)
    return render_slides(config, footer, nav)


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def internal_server_error(e: HTTPException) -> str:
    """Error pages."""
    title = f"{e.code} {e.name}"
    cover = {'title': title, 'doc': f"```sh\n{e.description}\n```"}
    slide_block(cover)
    return render_slides({'title': title, 'theme': 'night'}, {}, [cover])


def render_slides(config: _Data, footer: _Opt, nav: List[_HSlide]):
    """Rendered slides."""
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
        watermark_size=pixel(cast((int, str), config.get('watermark-size', ""))),
        history=str(cast(bool, config.get('history', True))).lower(),
        transition=cast(str, config.get('transition', 'linear')),
        slide_num=cast((str, bool), config.get('slide-num', 'c/t')),
        footer=footer,
        nav=nav
    )


def main() -> None:
    """Main function startup with SSH."""
    if '--freeze' in argv:
        app.config['FREEZER_RELATIVE_URLS'] = True
        Freezer(app).freeze()
        return
    from ssl import SSLContext, PROTOCOL_TLSv1_2
    context = SSLContext(PROTOCOL_TLSv1_2)
    context.load_cert_chain('localhost.crt', 'localhost.key')
    app.run(host='127.0.0.1', port=9443, debug=True, ssl_context=context)


if __name__ == "__main__":
    main()
