# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from typing import TypeVar, List, Dict, Union, Type
import ssl
from yaml import safe_load
from flask import Flask, render_template

_VSlide = Dict[str, str]
_HSlide = Dict[str, Union[str, List[_VSlide]]]
_Data = Dict[str, Union[str, bool, List[_HSlide]]]
T = TypeVar('T')

app = Flask(__name__)


def load_yaml() -> _Data:
    with open("settings.yml", 'r', encoding='utf-8') as f:
        return safe_load(f)


def check_type(t: Type[T], value: Union[str, bool, list, dict]) -> T:
    if not isinstance(value, t):
        raise TypeError(f"expect type: {t}, get: {type(value)}")
    return value


@app.route('/')
def presentation() -> str:
    settings = load_yaml()
    title = check_type(str, settings.get('title', "Untitled"))
    icon = check_type(str, settings.get('icon', "img/icon.png"))
    history = check_type(bool, settings.get('history', True))
    transition = check_type(str, settings.get('transition', 'linear'))
    nav: List[_HSlide] = check_type(list, settings.get('nav', []))
    for n in nav:
        n['title'] = check_type(str, n.get('title', ""))
        n['doc'] = check_type(str, n.get('doc', ""))
        sub_nav: List[_VSlide] = check_type(list, n.get('sub', []))
        for sn in sub_nav:
            sn['title'] = check_type(str, sn.get('title', ""))
            sn['doc'] = check_type(str, sn.get('doc', ""))
    return render_template(
        "presentation.html",
        title=title,
        icon=icon,
        history=str(history).lower(),
        transition=transition,
        nav=nav,
    )


def main() -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('localhost.crt', 'localhost.key')
    app.run(host='127.0.0.1', port=9443, debug=True, ssl_context=context)


if __name__ == "__main__":
    main()
