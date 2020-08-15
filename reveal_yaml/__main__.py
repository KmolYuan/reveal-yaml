# -*- coding: utf-8 -*-

__author__ = "Yuan Chang"
__copyright__ = "Copyright (C) 2019-2020"
__license__ = "MIT"
__email__ = "pyslvs@gmail.com"

from argparse import ArgumentParser
from os.path import join
from flask_frozen import Freezer
from reveal_yaml.app import PWD, app, serve, init


def main() -> None:
    """Main function startup with SSH."""
    parser = ArgumentParser(
        prog='Reveal.yaml',
        description="A YAML, Markdown, reveal.js based Flask application. "
                    "Supports gh-pages deployment actions.\n"
                    "https://kmolyuan.github.io/reveal-yaml",
        epilog=f"{__copyright__} {__license__} {__author__} {__email__}",
    )
    s = parser.add_subparsers(dest='cmd')
    initializer = s.add_parser('init', help="initialize a new project")
    initializer.add_argument('PATH', nargs='?', default=PWD, type=str,
                             help="project path")
    s.add_parser('pack', help="freeze the project (release)")
    server = s.add_parser('serve', help="serve the project")
    server.add_argument('--ip', default='localhost', type=str,
                        help="IP address")
    args = parser.parse_args()
    if args.cmd == 'init':
        init(args.PATH)
    elif args.cmd == 'pack':
        app.config['FREEZER_RELATIVE_URLS'] = True
        app.config['FREEZER_DESTINATION'] = join(PWD, 'build')
        Freezer(app).freeze()
    elif args.cmd == 'serve':
        serve(args.ip)


if __name__ == "__main__":
    main()
