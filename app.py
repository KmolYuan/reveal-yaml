# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import (
    cast, get_type_hints, overload, TypeVar, Tuple, List, Sequence, Dict,
    Mapping, Union, Type, Optional, Any,
)
from abc import ABCMeta
from dataclasses import dataclass, field, InitVar
from sys import argv
from urllib.parse import urlparse
from yaml import safe_load
from yaml.parser import ParserError
from flask import Flask, render_template, url_for, abort
from flask_frozen import Freezer, relative_url_for
from werkzeug.exceptions import HTTPException

_Opt = Mapping[str, str]
_Data = Dict[str, Any]
_YamlValue = Union[int, float, str, bool, list, dict]
T = TypeVar('T', bound=_YamlValue)
U = TypeVar('U', bound=_YamlValue)

app = Flask(__name__)


def load_yaml() -> _Data:
    """Load "reveal.yml" project."""
    with open("reveal.yml", 'r', encoding='utf-8') as f:
        return safe_load(f)


@overload
def cast_to(t: type, value: _YamlValue) -> Any:
    pass


@overload
def cast_to(t: Type[T], value: _YamlValue) -> T:
    pass


@overload
def cast_to(t: Tuple[Type[T], Type[U]], value: _YamlValue) -> Union[T, U]:
    pass


def cast_to(t, value):
    """Check value type."""
    if value is None:
        # Create an empty instance
        if isinstance(t, Sequence):
            t = t[0]
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


class TypeChecker(metaclass=ABCMeta):
    """Type checker function."""

    def __setattr__(self, key, value):
        t = get_type_hints(self.__class__)[key]
        if isinstance(t, type):
            value = cast_to(t, value)
        super(TypeChecker, self).__setattr__(key, value)


@dataclass(repr=False, eq=False)
class Size(TypeChecker):
    """The block has size attributes."""
    src: str = ""
    width: str = ""
    height: str = ""

    def __post_init__(self):
        """Replace URI."""
        self.src = uri(self.src)


@dataclass(repr=False, eq=False)
class Img(Size):
    """Image class."""
    label: str = ""


@dataclass(repr=False, eq=False)
class Footer(Img):
    """Footer class."""
    link: str = ""


@dataclass(repr=False, eq=False)
class Fragment(TypeChecker):
    """Fragment option."""
    img: str = ""
    math: str = ""
    youtube: str = ""
    embed: str = ""


@dataclass(repr=False, eq=False)
class Slide(TypeChecker):
    """Slide class."""
    id: str = ""
    title: str = ""
    doc: str = ""
    math: str = ""
    img: InitVar[List[Img]] = None
    youtube: InitVar[Size] = None
    embed: InitVar[Size] = None
    fragment: InitVar[Fragment] = None
    _img: List[Img] = field(init=False)
    _youtube: Size = field(init=False)
    _embed: Size = field(init=False)
    _fragment: Fragment = field(init=False)

    def __post_init__(self, img: Union[_Data, Sequence[_Data]],
                      youtube: _Opt, embed: _Opt, fragment: _Opt):
        """Check arguments after assigned."""
        if not isinstance(img, Sequence):
            _img = [cast(_Data, img)]
        if img is None:
            self._img = []
        else:
            self._img = [Img(**img or {}) for img in img]
        self._youtube = Size(**youtube or {})
        self._embed = Size(**embed or {})
        if not self._embed.width:
            self._embed.width = '1000px'
        if not self._embed.height:
            self._embed.height = '450px'
        self._fragment = Fragment(**fragment or {})


@dataclass(repr=False, eq=False)
class HSlide(Slide):
    """Root slide class."""
    sub: InitVar[List[Slide]] = None
    _sub: List[Slide] = field(init=False)

    def __post_init__(self, img: Any, youtube: _Opt, embed: _Opt,
                      fragment: _Opt, sub: Sequence[_Data]):
        """Check arguments after assigned."""
        super(HSlide, self).__post_init__(img, youtube, embed, fragment)
        if sub is None:
            self._sub = []
        else:
            self._sub = [Slide(**s or {}) for s in sub]


def outline(nav, nest) -> str:
    """Generate markdown outline."""
    doc = []
    for i, n in enumerate(nav[1:]):
        if n.title:
            doc.append(f"+ [{n.title}](#/{i + 1})")
        if not nest:
            continue
        for j, sn in enumerate(n._sub):
            if sn.title:
                doc.append("  " + f"+ [{sn.title}](#/{i + 1}/{j + 1})")
    return '\n'.join(doc)


@app.route('/')
def presentation() -> str:
    """Generate the presentation."""
    try:
        config = load_yaml()
    except ParserError as e:
        abort(500, e)
        return ""
    ol = cast_to(int, config.get('outline', 0))
    nav = cast_to(list, config.get('nav', []))
    for i in range(len(nav)):
        nav[i] = HSlide(**nav[i] or {})
    if nav[1:] and ol > 0:
        nav[0]._sub.append(Slide(title="Outline", doc=outline(nav, ol >= 2)))
    return render_slides(config, nav, Footer(**config.get('footer', {})))


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def internal_server_error(e: HTTPException) -> str:
    """Error pages."""
    title = f"{e.code} {e.name}"
    return render_slides(
        {'title': title, 'theme': 'night'},
        [HSlide(title=title, doc=f"```sh\n{e.description}\n```")]
    )


def render_slides(config: _Data, nav: Sequence[HSlide],
                  footer: Optional[Footer] = None):
    """Rendered slides."""
    if footer is None:
        footer = Footer()
    return render_template(
        "presentation.html",
        title=cast_to(str, config.get('title', "Untitled")),
        description=cast_to(str, config.get('description', "")),
        author=cast_to(str, config.get('author', "")),
        theme=cast_to(str, config.get('theme', 'serif')),
        icon=uri(cast_to(str, config.get('icon', "img/icon.png"))),
        default_style=cast_to(bool, config.get('default-style', True)),
        extra_style=cast_to(str, config.get('extra-style', "")),
        watermark=uri(cast_to(str, config.get('watermark', ""))),
        watermark_size=pixel(
            cast_to((int, str), config.get('watermark-size', ""))),
        history=str(cast_to(bool, config.get('history', True))).lower(),
        transition=cast_to(str, config.get('transition', 'linear')),
        slide_num=cast_to((str, bool), config.get('slide-num', 'c/t')),
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
