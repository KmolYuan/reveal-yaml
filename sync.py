# -*- coding: utf-8 -*-

from os.path import isdir
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
import yaml
import json


def main():
    if not isdir("reveal.js/dist"):
        raise FileNotFoundError("submodules are not fetched yet")
    for path in ("reveal.js", "css", "plugin"):
        if path == "reveal.js":
            copy_tree("reveal.js/dist", f"reveal_yaml/static/{path}")
        else:
            copy_tree(f"reveal.js/{path}", f"reveal_yaml/static/{path}")
    mkpath("reveal_yaml/static/js")
    copy_file("jquery/dist/jquery.min.js", "reveal_yaml/static/js")
    mkpath("reveal_yaml/static/ace")
    copy_file("ace/src-min-noconflict/ace.js", "reveal_yaml/static/ace")
    copy_file("ace/src-min-noconflict/mode-yaml.js",
              "reveal_yaml/static/ace")
    copy_file("ace/src-min-noconflict/theme-chrome.js",
              "reveal_yaml/static/ace")
    # Generate JSON schema
    with open("reveal_yaml/schema.yaml", 'r') as f:
        data = yaml.safe_load(f)
    with open("reveal_yaml/schema.json", 'w+') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    main()
