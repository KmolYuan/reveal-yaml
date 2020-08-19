# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import (
    cast, get_type_hints, overload, TypeVar, List, Sequence, Dict, Mapping,
    Union, Type, Any,
)
from abc import ABCMeta
from dataclasses import dataclass, field, is_dataclass, InitVar
from sys import stdout
from os.path import isfile, join
from urllib.parse import urlparse
from yaml import safe_load
from flask import Flask, render_template, url_for
from flask_frozen import relative_url_for
from werkzeug.exceptions import HTTPException

_Opt = Mapping[str, str]
_Data = Dict[str, Any]
_YamlValue = Union[bool, int, float, str, list, dict]
T = TypeVar('T', bound=Union[_YamlValue, 'TypeChecker'])
U = TypeVar('U', bound=_YamlValue)

PROJECT = ""
app = Flask(__name__)


def load_yaml() -> _Data:
    """Load project."""
    with open(PROJECT, 'r', encoding='utf-8') as f:
        data: _Data = safe_load(f)
    for key in tuple(data):
        data[key.replace('-', '_')] = data.pop(key)
    return data


@overload
def cast_to(key: str, t: Type[List[T]], value: _YamlValue) -> List[T]:
    pass


@overload
def cast_to(key: str, t: Type[T], value: _YamlValue) -> T:
    pass


def cast_to(key, t, value):
    """Check value type."""
    if hasattr(t, '__origin__') and t.__origin__ is list:
        # Is listed items
        t = t.__args__[0]
        if issubclass(t, TypeChecker) and is_dataclass(t):
            return t.as_list(value)
        else:
            return [cast_to(t, v) for v in value]
    elif isinstance(value, t):
        return value
    elif (
        issubclass(t, TypeChecker)
        and is_dataclass(t)
        and isinstance(value, dict)
    ):
        return t.from_dict(value)
    raise TypeError(f"'{key}' expect type: {t}, got: {type(value)}")


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
    Self = TypeVar('Self', bound='TypeChecker')
    MaybeDict = Union[_Data, Self]
    MaybeList = Union[_Data, Sequence[_Data], Self, Sequence[Self]]

    @classmethod
    def from_dict(cls: Type[Self], data: MaybeDict) -> Self:
        """Generate a data class from dict object."""
        if isinstance(data, cls):
            return data
        if not isinstance(data, Mapping):
            raise TypeError(f"expect type: {cls}, wrong type: {type(data)}")
        if not data:
            raise TypeError(f"expect type: {cls}, the field cannot be empty")
        return cls(**data)  # type: ignore

    @classmethod
    def as_list(cls: Type[Self], data: MaybeList) -> List[Self]:
        """Generate a list of Self from dict object."""
        if isinstance(data, cls):
            return [data]
        if not isinstance(data, Sequence):
            data = [cast(_Data, data)]
        return [cls.from_dict(d) for d in data]

    def __setattr__(self, key, value):
        super(TypeChecker, self).__setattr__(key, cast_to(
            key, get_type_hints(self.__class__).get(key, None), value))


@dataclass(repr=False, eq=False)
class Size(TypeChecker):
    """The block has size attributes."""
    src: str = ""
    width: str = ""
    height: str = ""

    def __post_init__(self):
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
    include: InitVar[str] = None

    def __post_init__(self, include):
        if include is not None:
            with open(join("templates", include), 'r') as f:
                self.doc += '\n\n' + f.read()
        if not self.embed.width:
            self.embed.width = '1000px'
        if not self.embed.height:
            self.embed.height = '450px'


@dataclass(repr=False, eq=False)
class HSlide(Slide):
    """Root slide class."""
    sub: List[Slide] = field(default_factory=list)


@dataclass(repr=False, eq=False)
class Config(TypeChecker):
    lang: str = "en"
    title: str = ""
    description: str = ""
    author: str = ""
    theme: str = "serif"
    code_theme: str = "zenburn"
    icon: str = "img/icon.png"
    outline: int = 2
    default_style: bool = True
    extra_style: str = ""
    watermark: str = ""
    watermark_size: str = ""
    nav_mode: str = "default"
    show_arrows: bool = True
    center: bool = True
    loop: bool = False
    history: bool = True
    slide_num: str = "c/t"
    progress: bool = True
    mouse_wheel: bool = False
    preview_links: bool = False
    transition: str = "slide"
    footer: Footer = field(default_factory=Footer)
    nav: List[HSlide] = field(default_factory=list)

    def __post_init__(self):
        """Check arguments after assigned."""
        if not self.title and self.nav:
            self.title = self.nav[0].title
        self.icon = uri(self.icon)
        self.watermark = uri(self.watermark)
        self.watermark_size = pixel(self.watermark_size)
        if self.extra_style:
            with open(join("templates", self.extra_style), 'r') as f:
                self.extra_style = f.read()
        if self.outline not in {0, 1, 2}:
            raise ValueError(f"outline level should be 0, 1 or 2, "
                             f"not {self.outline}")
        if not self.nav[1:] or self.outline == 0:
            return
        # Make an outline page
        doc = []
        for i, n in enumerate(self.nav[1:]):
            if n.title:
                if self.history:
                    title = f"+ [{n.title}](#/{i + 1})"
                else:
                    title = f"+ {n.title}"
                doc.append(title)
            if self.outline < 2:
                continue
            for j, sn in enumerate(n.sub):
                if sn.title:
                    if self.history:
                        title = f"+ [{sn.title}](#/{i + 1}/{j + 1})"
                    else:
                        title = f"+ {sn.title}"
                    doc.append(" " * 2 + title)
        self.nav[0].sub.append(Slide(title="Outline", doc='\n'.join(doc)))


@app.route('/')
def presentation() -> str:
    """Generate the presentation."""
    return render_slides(Config(**load_yaml()))


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(410)
@app.errorhandler(500)
def internal_server_error(e: HTTPException) -> str:
    """Error pages."""
    from traceback import format_exc
    title = f"{e.code} {e.name}"
    return render_slides(
        Config(title=title, theme='night', nav=[HSlide(
            title=title,
            doc=f"```sh\n{format_exc()}\n{e.description}\n```"
        )]))


def render_slides(config: Config) -> str:
    """Rendered slides."""
    return render_template("slides.html", config=config)


def find_project(pwd: str) -> None:
    """Get project name from the current path."""
    global PROJECT
    PROJECT = join(pwd, "reveal.yaml")
    if not isfile(PROJECT):
        PROJECT = join(pwd, "reveal.yml")
    app.config['STATIC_FOLDER'] = join(pwd, 'static')


def serve(pwd: str, ip: str, port: int) -> None:
    """Start server."""
    find_project(pwd)
    if not isfile(PROJECT):
        stdout.write("fatal: project is not found")
        return
    key = (join(pwd, 'localhost.crt'), join(pwd, 'localhost.key'))
    if isfile(key[0]) and isfile(key[1]):
        from ssl import SSLContext, PROTOCOL_TLSv1_2
        context = SSLContext(PROTOCOL_TLSv1_2)
        context.load_cert_chain(key[0], key[1])
        app.run(ip, port, ssl_context=context)
    else:
        app.run(ip, port)
