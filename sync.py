# -*- coding: utf-8 -*-

from os import remove
from shutil import rmtree
from distutils.dir_util import copy_tree, mkpath
from glob import glob
from urllib.request import urlretrieve
from tarfile import open as tgz
import yaml
import json


def reveal_cdn(ver: str) -> None:
    """Download Reveal.js from npm.js."""
    urlretrieve(f"https://registry.npmjs.org/reveal.js/-/reveal.js-{ver}.tgz",
                'reveal.tgz')
    with tgz('reveal.tgz', 'r:gz') as f:
        f.extractall()
    remove('reveal.tgz')
    for f in glob("package/**/*.esm.js*", recursive=True):
        remove(f)
    copy_tree("package/dist", f"reveal_yaml/static/reveal.js")
    copy_tree("package/plugin", f"reveal_yaml/static/plugin")
    rmtree("package")


def cdn(url: str, to: str) -> None:
    """Download from CDNjs."""
    to += url.rsplit('/', maxsplit=1)[-1]
    urlretrieve("https://cdnjs.cloudflare.com/ajax/libs/" + url, to)


def main():
    reveal_cdn("4.0.2")
    path = "reveal_yaml/static/js/"
    mkpath(path)
    cdn("jquery/3.5.1/jquery.min.js", path)
    path = "reveal_yaml/static/ace/"
    mkpath(path)
    cdn("ace/1.4.12/ace.min.js", path)
    cdn("ace/1.4.12/ext-searchbox.min.js", path)
    cdn("ace/1.4.12/ext-whitespace.min.js", path)
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
