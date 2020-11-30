# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from argparse import ArgumentParser
from sys import stdout
from os import getcwd
from os.path import join, abspath, dirname, isfile, isdir
from argcomplete import autocomplete
from reveal_yaml import __version__


def main() -> None:
    """Main function.

    Module imports should be placed after commands to ensure the performance.
    """
    root = abspath(dirname(__file__))
    pwd = abspath(getcwd())
    ver = f"Reveal.yaml Manager v{__version__}"
    parser = ArgumentParser(
        prog=ver,
        description="A YAML, Markdown, reveal.js based Flask application. "
                    "Supports gh-pages deployment actions. "
                    "https://kmolyuan.github.io/reveal-yaml",
        epilog=f"{__copyright__} {__license__} {__author__} {__email__}",
    )
    parser.add_argument('-v', '--version', action='version', version=ver)
    s = parser.add_subparsers(dest='cmd')
    sub = s.add_parser('init', help="initialize a new project")
    sub.add_argument('PATH', nargs='?', default=pwd, type=str,
                     help="project path")
    sub.add_argument('--no-workflow', action='store_true',
                     help="don't generate Github workflow")
    sub = s.add_parser('pack', help="freeze to a static project")
    sub.add_argument('PATH', nargs='?', default=pwd, type=str,
                     help="project path")
    sub.add_argument('-o', '--dist', nargs='?', default="", type=str,
                     help="dist path")
    for cmd, doc in (
        ('serve', "project"),
        ('editor', "project for edit mode (preserve)"),
        ('doc', "documentation"),
    ):
        sub = s.add_parser(cmd, help=f"serve the {doc}")
        if cmd != 'doc':
            sub.add_argument('PATH', nargs='?', default=pwd, type=str,
                             help="project path")
        sub.add_argument('--ip', default='localhost', type=str,
                         help="IP address")
        sub.add_argument('--port', default=0, type=int, help="specified port")
    autocomplete(parser)
    args = parser.parse_args()
    if args.cmd == 'init':
        # Create a project
        from distutils.file_util import copy_file
        from distutils.dir_util import mkpath, copy_tree
        args.PATH = abspath(args.PATH)
        mkpath(args.PATH)
        static_path = join(args.PATH, 'static')
        if not isdir(static_path):
            mkpath(static_path)
        for name in ('js', 'plugin', 'reveal.js'):
            copy_tree(join(root, 'static', name), join(static_path, name))
        workflow = join(args.PATH, ".github", "workflows", "deploy.yaml")
        if not args.no_workflow and not isfile(workflow):
            mkpath(dirname(workflow))
            copy_file(join(root, "deploy.yaml"), workflow)
        if not (isfile(join(args.PATH, "reveal.yaml"))
                or isfile(join(args.PATH, "reveal.yml"))):
            copy_file(join(root, "blank.yaml"), join(args.PATH, "reveal.yaml"))
    elif args.cmd == 'pack':
        from reveal_yaml.slides import find_project, pack
        from reveal_yaml.slides_app import app
        args.PATH = abspath(args.PATH)
        if not find_project(app, args.PATH):
            stdout.write("fatal: project is not found")
            return
        if not args.dist:
            args.dist = join(args.PATH, 'build')
        pack(args.PATH, args.dist, app)
    elif args.cmd in {'serve', 'editor', 'doc'}:
        from reveal_yaml.slides import find_project
        args.PATH = root if args.cmd == 'doc' else abspath(args.PATH)
        if args.cmd == 'editor':
            from reveal_yaml.editor import app  # type: ignore
        else:
            from reveal_yaml.slides_app import app
            if not find_project(app, args.PATH):
                stdout.write("fatal: project is not found")
                return
        from reveal_yaml.utility import serve
        serve(args.PATH, app, args.ip, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
