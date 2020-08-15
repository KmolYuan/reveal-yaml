# -*- coding: utf-8 -*-

from os.path import isdir
from distutils.dir_util import mkpath, copy_tree


def main():
    if not isdir("reveal.js/dist"):
        raise FileNotFoundError("submodules are not fetched yet")
    for path in ("reveal.js", "css", "plugin"):
        if path == "reveal.js":
            copy_tree("reveal.js/dist", f"reveal_yaml/static/{path}")
        else:
            copy_tree(f"reveal.js/{path}", f"reveal_yaml/static/{path}")


if __name__ == '__main__':
    main()
