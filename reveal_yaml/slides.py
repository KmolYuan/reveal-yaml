# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import (
    cast, get_type_hints, overload, TypeVar, Tuple, List, Sequence, Dict,
    Mapping, OrderedDict, Iterator, ItemsView, Union, Type, Any,
)
from abc import ABCMeta
from dataclasses import dataclass, field, is_dataclass, asdict
from os.path import isfile, join, relpath, dirname, sep
from distutils.dir_util import copy_tree, mkpath
from shutil import rmtree
from yaml import safe_load
from json import loads
from jsonschema import validate
from flask import Flask, render_template, url_for
from .utility import is_url, valid_config, load_file, dl, rm, ROOT

_Opt = Mapping[str, str]
_Data = Dict[str, Any]
_YamlValue = Union[bool, int, float, str, list, dict]
_PROJECT = ""
T = TypeVar('T', bound=Union[_YamlValue, 'TypeChecker'])
U = TypeVar('U', bound=_YamlValue)


def load_yaml() -> _Data:
    """Load project."""
    config = valid_config(safe_load(load_file(_PROJECT)))
    validate(config, loads(load_file(join(ROOT, 'schema.json'))))
    return config


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
            return [cast_to(key, t, v) for v in value]
    elif isinstance(value, t):
        return value
    elif (
        issubclass(t, TypeChecker)
        and is_dataclass(t)
        and isinstance(value, dict)
    ):
        return t.from_dict(value)
    raise TypeError(f"'{key}' expect type: {t}, got: {type(value)}")


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
    include: str = ""
    math: str = ""
    img: List[Img] = field(default_factory=list)
    youtube: Size = field(default_factory=Size)
    embed: Size = field(default_factory=Size)
    fragment: Fragment = field(default_factory=Fragment)

    def __post_init__(self):
        if not self.embed.width:
            self.embed.width = '1000px'
        if not self.embed.height:
            self.embed.height = '450px'

    @property
    def is_article(self) -> bool:
        """Return true if the block is empty."""
        return bool(self.title) and any((self.doc, self.include, self.math,
                                         self.img, self.youtube.src,
                                         self.embed.src))


@dataclass(repr=False, eq=False)
class HSlide(Slide):
    """Root slide class."""
    sub: List[Slide] = field(default_factory=list)


@dataclass(repr=False, eq=False)
class Plugin(TypeChecker):
    """Plugin enable / disable options."""
    zoom: bool = False
    notes: bool = True
    search: bool = False
    markdown: bool = field(default=True, init=False)
    highlight: bool = True
    math: bool = False

    def as_dict(self) -> ItemsView[str, bool]:
        """Return self as mapping."""
        return asdict(self, dict_factory=OrderedDict[str, bool]).items()


@dataclass(repr=False, eq=False)
class Config(TypeChecker):
    """Config overview."""
    lang: str = "en"
    title: str = ""
    description: str = ""
    author: str = ""
    cdn: str = ""
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
    plugin: Plugin = field(default_factory=Plugin)

    def __post_init__(self):
        """Check arguments after assigned."""
        if not self.title and self.nav:
            self.title = self.nav[0].title
        self.cdn = self.cdn.rstrip('/')
        self.watermark_size = pixel(self.watermark_size)
        if self.outline not in {0, 1, 2}:
            raise ValueError(f"outline level should be 0, 1 or 2, "
                             f"not {self.outline}")
        # Make an outline page
        doc = []
        for i, j, n in self.slides:
            if not self.plugin.math and n.math:
                self.plugin.math = True
            if i < 1 or not n.title or self.outline < 1:
                continue
            doc.append(" " * (2 if j > 0 else 0) + (
                f"+ [{n.title}](#/{f'{i}/{j}' if j > 0 else f'{i}'})"
                if self.history else
                f"+ {n.title}"
            ))
        if doc:
            self.nav[0].sub.append(Slide(title="Outline", doc='\n'.join(doc)))

    @property
    def slides(self) -> Iterator[Tuple[int, int, Slide]]:
        """Traverse all slides."""
        for i, n in enumerate(self.nav):
            yield i, 0, n
            for j, sn in enumerate(n.sub):
                yield i, j + 1, sn


def render_slides(config: Config, *, rel_url: bool = False) -> str:
    """Rendered slides."""
    if rel_url:
        def url_func(endpoint: str, *, filename: str) -> str:
            """Generate relative internal path."""
            path = join(ROOT, endpoint, filename).replace('/', sep)
            return relpath(path, ROOT).replace(sep, '/')
    else:
        url_func = url_for
    project_dir = dirname(_PROJECT)

    def uri(path: str) -> str:
        """Handle the relative path and URIs."""
        if not path:
            return ""
        if is_url(path):
            return path
        if (
            not rel_url
            and config.cdn
            # Prefer to load local files
            # Check files when reloading
            and not isfile(join(project_dir, 'static', path))
        ):
            return f"{config.cdn}/{path}"
        return url_func('static', filename=path)

    def include(path: str) -> str:
        """Include text file."""
        return load_file(join(project_dir, uri(path).strip('/')))

    return render_template("slides.html", config=config, url_for=url_func,
                           uri=uri, include=include)


def find_project(flask_app: Flask, pwd: str) -> str:
    """Get project name from the current path."""
    project = join(pwd, "reveal.yaml")
    if not isfile(project):
        project = join(pwd, "reveal.yml")
    if not isfile(project):
        return ""
    flask_app.config['STATIC_FOLDER'] = join(pwd, 'static')
    global _PROJECT
    _PROJECT = project
    return _PROJECT


def pack(root: str, build_path: str, app: Flask) -> None:
    """Pack into a static project."""
    with app.app_context():
        copy_project(Config(**load_yaml()), root, build_path)


def copy_project(config: Config, root: str, build_path: str) -> None:
    """Copy project."""
    mkpath(build_path)
    copy_tree(join(root, 'static'), join(build_path, 'static'))

    # Download from CDN
    def cdn(src: str) -> None:
        """Download from source path."""
        if src and not is_url(src):
            dl(f"{config.cdn}/{src}", join(build_path, 'static', src))

    cdn(config.icon)
    cdn(config.watermark)
    for _, _, n in config.slides:
        for img in n.img:
            cdn(img.src)
        cdn(n.embed.src)
    # Render index.html
    with open(join(build_path, "index.html"), 'w+', encoding='utf-8') as f:
        f.write(render_slides(config, rel_url=True))
    # Remove include files
    rm(join(build_path, 'static', config.extra_style))
    for _, _, n in config.slides:
        rm(join(build_path, 'static', n.include))
    # Remove unused js module
    rmtree(join(build_path, 'static', 'ace'), ignore_errors=True)
    for name, enabled in config.plugin.as_dict():
        if not enabled:
            rmtree(join(build_path, 'static', 'plugin', name))
