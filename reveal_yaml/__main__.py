# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from argparse import ArgumentParser
from os import getcwd
from os.path import join, abspath, dirname, isfile


def main() -> None:
    """Main function startup with SSH."""
    pwd = abspath(getcwd())
    parser = ArgumentParser(
        prog='Reveal.yaml',
        description="A YAML, Markdown, reveal.js based Flask application. "
                    "Supports gh-pages deployment actions.\n"
                    "https://kmolyuan.github.io/reveal-yaml",
        epilog=f"{__copyright__} {__license__} {__author__} {__email__}",
    )
    s = parser.add_subparsers(dest='cmd')
    sub = s.add_parser('init', help="initialize a new project")
    sub.add_argument('PATH', nargs='?', default=pwd, type=str,
                     help="project path")
    sub.add_argument('--no-workflow', action='store_true',
                     help="don't generate Github workflow")
    sub = s.add_parser('pack', help="freeze to a static project")
    sub.add_argument('PATH', nargs='?', default=join(pwd, 'build'), type=str,
                     help="dist path")
    sub = s.add_parser('serve', help="serve the project")
    sub.add_argument('IP', nargs='?', default='localhost', type=str,
                     help="IP address")
    sub.add_argument('--port', default=0, type=int, help="specified port")
    args = parser.parse_args()
    if args.cmd == 'init':
        # Create a project
        from distutils.file_util import copy_file
        from distutils.dir_util import mkpath, copy_tree
        root = abspath(dirname(__file__))
        mkpath(args.PATH)
        copy_tree(join(root, "static"), join(args.PATH, "static"))
        mkpath(join(args.PATH, "templates"))
        workflow = join(".github", "workflows", "deploy.yaml")
        if not args.no_workflow and not isfile(workflow):
            mkpath(join(args.PATH, dirname(workflow)))
            copy_file(join(root, workflow), join(args.PATH, workflow))
        if not isfile("reveal.yaml") and not isfile("reveal.yml"):
            copy_file(join(root, "blank.yaml"), join(args.PATH, "reveal.yaml"))
    elif args.cmd == 'pack':
        # Pack into a static project
        from reveal_yaml.app import app
        from flask_frozen import Freezer
        app.config['FREEZER_RELATIVE_URLS'] = True
        app.config['FREEZER_DESTINATION'] = args.PATH
        Freezer(app).freeze()
    elif args.cmd == 'serve':
        from reveal_yaml.app import serve
        serve(pwd, args.IP, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
