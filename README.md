# Reveal.yaml

[![PyPI](https://img.shields.io/pypi/v/reveal-yaml.svg)](https://pypi.org/project/reveal-yaml/)

See the [documentation](https://kmolyuan.github.io/reveal-yaml/).

This project is under MIT license.

Quickly create a Reveal.js writing environment!

```bash
rym init myproject
rym serve --port=5000
```

Then start writing the slides in YAML + Markdown.

## Editor

[Heroku version](https://reveal-yaml.herokuapp.com/).

Start it with CLI:

```bash
rym editor --port=5000
```

## JSON Schema

+ [schema.json](https://raw.githubusercontent.com/KmolYuan/reveal-yaml/gh-pages/schema.json)
+ [schema.yaml](https://raw.githubusercontent.com/KmolYuan/reveal-yaml/master/reveal_yaml/schema.yaml)

## Deployment

Build to a static HTML format: (`index.html` and `static` folder)

```bash
rym pack
```

A Github workflow `.github/workflows/deploy.yml` generated by `rym init`
can also be used on your repository.
