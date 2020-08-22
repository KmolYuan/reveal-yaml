# -*- coding: utf-8 -*-

from os.path import isdir
from distutils.dir_util import copy_tree, mkpath
from urllib.request import urlretrieve
import yaml
import json


def cdn(url: str, to: str) -> None:
    """Download from CDNjs."""
    to += url.rsplit('/', maxsplit=1)[-1]
    urlretrieve("https://cdnjs.cloudflare.com/ajax/libs/" + url, to)


def main():
    if not isdir("reveal.js/dist"):
        raise FileNotFoundError("submodules are not fetched yet")
    for path in ("reveal.js", "css", "plugin"):
        if path == "reveal.js":
            copy_tree("reveal.js/dist", f"reveal_yaml/static/{path}")
        else:
            copy_tree(f"reveal.js/{path}", f"reveal_yaml/static/{path}")
    path = "reveal_yaml/static/js/"
    mkpath(path)
    cdn("jquery/3.5.1/jquery.min.js", path)
    path = "reveal_yaml/static/ace/"
    mkpath(path)
    cdn("ace/1.4.12/ace.min.js", path)
    cdn("ace/1.4.12/ext-searchbox.min.js", path)
    cdn("ace/1.4.12/ext-whitespace.min.js", path)
    cdn("ace/1.4.12/ext-keybinding_menu.min.js", path)
    cdn("ace/1.4.12/ext-language_tools.min.js", path)
    cdn("ace/1.4.12/mode-yaml.min.js", path)
    cdn("ace/1.4.12/theme-chrome.min.js", path)
    cdn("ace/1.4.12/theme-monokai.min.js", path)
    # Generate JSON schema
    with open("reveal_yaml/schema.yaml", 'r') as f:
        data = yaml.safe_load(f)
    with open("reveal_yaml/schema.json", 'w+') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    main()
