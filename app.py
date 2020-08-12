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
from dataclasses import dataclass, field, is_dataclass
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
Self = TypeVar('Self')
_MaybeDict = Union[_Data, Self]
_MaybeList = Union[_Data, Sequence[_Data], Sequence[Self], Self]
T = TypeVar('T', bound=_YamlValue)
U = TypeVar('U', bound=_YamlValue)

app = Flask(__name__)


def load_yaml() -> _Data:
    """Load "reveal.yml" project."""
    with open("reveal.yml", 'r', encoding='utf-8') as f:
        return safe_load(f)


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
    elif is_dataclass(t) and isinstance(value, dict):
        return value
    elif isinstance(value, t):
        return value
    else:
        abort(500, f"expect type: {t}, get: {type(value)}")


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

    @classmethod
    def from_dict(cls: Type[Self], data: _MaybeDict) -> Self:
        """Generate data class from dict object."""
        if isinstance(data, cls):
            return data
        return cls(**data or {})  # type: ignore

    @classmethod
    def from_list(cls: Type[Self], data: _MaybeList) -> List[Self]:
        """Generate list of Self from dict object."""
        if isinstance(data, cls):
            return [data]
        if not isinstance(data, Sequence):
            data = [cast(_Data, data)]
        return [cls(**d or {}) for d in data]  # type: ignore

    def __setattr__(self, key, value):
        t = get_type_hints(self.__class__)[key]
        if t in {str, bytes, int, float, bool}:
            # Cast only basic types, others will be handled by their classes
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
        self.width = pixel(self.width)
        self.height = pixel(self.height)


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
    img: List[Img] = field(default_factory=list)
    youtube: Size = field(default_factory=Size)
    embed: Size = field(default_factory=Size)
    fragment: Fragment = field(default_factory=Fragment)

    def __post_init__(self):
        """Check arguments after assigned."""
        self.img = Img.from_list(self.img)
        self.youtube = Size.from_dict(self.youtube)
        self.embed = Size.from_dict(self.embed)
        if not self.embed.width:
            self.embed.width = '1000px'
        if not self.embed.height:
            self.embed.height = '450px'
        self.fragment = Fragment.from_dict(self.fragment)


@dataclass(repr=False, eq=False)
class HSlide(Slide):
    """Root slide class."""
    sub: List[Slide] = field(default_factory=list)

    def __post_init__(self):
        """Check arguments after assigned."""
        super(HSlide, self).__post_init__()
        self.sub = Slide.from_list(self.sub)


def outline(nav, nest) -> str:
    """Generate markdown outline."""
    doc = []
    for i, n in enumerate(nav[1:]):
        if n.title:
            doc.append(f"+ [{n.title}](#/{i + 1})")
        if not nest:
            continue
        for j, sn in enumerate(n.sub):
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
    else:
        ol = cast_to(int, config.get('outline', 0))
        nav = cast_to(list, config.get('nav', []))
        for i in range(len(nav)):
            nav[i] = HSlide(**nav[i] or {})
        if nav[1:] and ol > 0:
            nav[0].sub.append(Slide(title="Outline", doc=outline(nav, ol >= 2)))
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
    # TODO: Simplify options with a data class
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
